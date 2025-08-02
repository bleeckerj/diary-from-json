from fpdf import FPDF
from PIL import Image
import json
import io
import os
import base64
import logging 
import argparse

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s [%(name)s][Line %(lineno)d]: %(message)s'
)

logging.getLogger("fpdf").setLevel(logging.WARNING)
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

GAP_BETWEEN_ENTRIES_MM = 12  # or any value in millimeters you prefer

PAGE_SIZES = {
    "A4": (210, 297),
    "A5": (148, 210),
    "LETTER": (216, 279),
    "LEGAL": (216, 356),
    "TABLOID": (279, 432)
}

DPI = 300  # Print resolution

def mm_to_px(mm):
    return int(mm / 25.4 * DPI)

def px_to_mm(px):
    return px * 25.4 / DPI

def decode_base64_image(image_data, image_type):
    # Extract base64 from markdown-style ![](data:image/TYPE;base64,....)
    import re
    match = re.search(r'base64,([A-Za-z0-9+/=\n\r]+)\)', image_data)
    if not match:
        return None
    b64 = match.group(1)
    try:
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes))
        # Convert to CMYK for print
        if img.mode != "CMYK":
            img = img.convert("CMYK")
        return img
    except Exception as e:
        logging.error(f"decode_base64_image error: {e}\nImage data: {image_data[:100]}...")
        return None
def pt_to_mm(pt):
    """Convert points to millimeters."""
    return pt * 0.352778

def inch_to_mm(inch):
    return inch * 25.4

def add_entry_to_pdf(pdf, entry, config):
    margin = config.get("margin_mm", 8.89)  # Default to 0.35 inch in mm
    page_w = config["page_size"][0]
    avail_w_mm = page_w - 2 * margin

    # Date: colored rectangle full width (respecting margins), white text
    rect_height_mm = pt_to_mm(config["date_font_size"]) * config["line_spacing"] * 1.5
    pdf.set_fill_color(0, 0, 0)  # Black in RGB
    pdf.rect(x=margin, y=pdf.get_y(), w=avail_w_mm, h=rect_height_mm, style='F')
    pdf.set_xy(margin, pdf.get_y())
    pdf.set_text_color(255, 255, 255)  # White text (RGB)
    pdf.set_font(config["date_font"], size=config["date_font_size"])
    date_text = entry["dateline"]
    pdf.cell(avail_w_mm, rect_height_mm, date_text, ln=True, align='L')
    pdf.set_text_color(0, 0, 0)  # Reset to black for body text
    pdf.ln(rect_height_mm * 0.2)

    # Text: treat each text_obj as a paragraph, let multi_cell handle wrapping
    pdf.set_font(config["text_font"], size=config["text_font_size"])
    line_height_mm = pt_to_mm(config["text_font_size"]) * config["line_spacing"]
    for text_obj in entry["text"]:
        paragraph = text_obj["text"]
        try:
            pdf.multi_cell(avail_w_mm, line_height_mm, paragraph)
            pdf.ln(line_height_mm)
        except Exception as e:
            logging.error(
                f"[FPDFException] {e}\n"
                f"Problematic text: {repr(paragraph)}\n"
                f"Dateline: {repr(entry['dateline'])}\nFull text_obj: {repr(text_obj)}"
            )

    # Images: scale to available width, maintain aspect ratio
    for idx, img in enumerate(entry.get("images", [])):
        image_type = img.get("type", "png")
        image_data = img.get("image_data", "")
        pil_img = decode_base64_image(image_data, image_type)
        if pil_img:
            page_w, page_h = config["page_size"]
            max_w_mm = page_w - 2 * margin  # scale to full available width
            w, h = pil_img.size
            max_w_px = mm_to_px(max_w_mm)
            ratio = max_w_px / w if w > 0 else 1
            new_w_px = int(w * ratio)
            new_h_px = int(h * ratio)
            pil_img = pil_img.resize((new_w_px, new_h_px), Image.LANCZOS)
            img_buffer = io.BytesIO()
            pil_img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            try:
                pdf.image(img_buffer, x=margin, w=max_w_mm, h=px_to_mm(new_h_px))
                pdf.ln(px_to_mm(new_h_px) + line_height_mm)
            except Exception as e:
                logging.error(
                    f"[Image Error] {e}\n"
                    f"Image index: {idx}\nDateline: {repr(entry['dateline'])}\nImage metadata: {repr(img)}"
                )
    # Add vertical gap after each diary entry
    pdf.ln(GAP_BETWEEN_ENTRIES_MM)

def create_pdf_from_json(json_path, output_pdf, page_size="A5", date_font="DejaVuSans", date_font_size=18, text_font="DejaVuSans", text_font_size=12, line_spacing=1.3, margin_inch=0.35):
    margin_mm = inch_to_mm(margin_inch)
    config = {
        "page_size": PAGE_SIZES.get(page_size.upper(), PAGE_SIZES["A5"]),
        "date_font": date_font,
        "date_font_size": date_font_size,
        "text_font": text_font,
        "text_font_size": text_font_size,
        "line_spacing": line_spacing,
        "margin_mm": margin_mm
    }
    pdf = FPDF(unit="mm", format=config["page_size"])
    # Register DejaVuSans font for Unicode support
    font_path = "/Users/julian/Dropbox (Personal)/Projects By Year/@2025/OMATA Process Diary/ProcessDiaryEntries/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf"
    pdf.add_font("DejaVuSans", "", font_path)
    pdf.add_page()  # Ensure at least one page is open before writing
    # Load diary JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        diary = json.load(f)
    for entry in diary["entries"]:
        add_entry_to_pdf(pdf, entry, config)
    pdf.output(output_pdf)
    logging.info(f"Created {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--margin", type=float, default=0.35, help="Margin in inches (default: 0.35)")
    args = parser.parse_args()
    create_pdf_from_json(
        "OMATA-NOTES  Continued At Week 182.json",
        "OMATA_Diary_Print.pdf",
        page_size="A5",
        date_font="DejaVuSans",
        date_font_size=12,
        text_font="DejaVuSans",
        text_font_size=9,
        line_spacing=1,
        margin_inch=args.margin
    )