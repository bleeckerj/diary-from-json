from fpdf import FPDF
from PIL import Image
import json
import io
import os
import base64
import logging 
import argparse
import re

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
    "A6": (105, 148),
    "A7": (74, 105),
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
    margin = config.get("margin_mm", 8.89)
    page_w = config["page_size"][0]
    page_h = config["page_size"][1]
    avail_w_mm = page_w - 2 * margin

    # Heights
    rect_height_mm = pt_to_mm(config["date_font_size"]) * config["line_spacing"] * 1.5
    date_gap_mm = rect_height_mm * 2  # vertical gap after dateline
    line_height_mm = pt_to_mm(config["text_font_size"]) * config["line_spacing"]

    # Minimum block: dateline + gap + at least 5 lines of text
    min_text_lines = 5
    min_block_height = rect_height_mm + date_gap_mm + (line_height_mm * min_text_lines)

    current_y = pdf.get_y()
    usable_page_height = page_h - margin
    remaining_space = usable_page_height - current_y

    # Force page break if not enough space for dateline + gap + minimum text
    if remaining_space < min_block_height:
        pdf.add_page()
        pdf.set_y(margin)

    # Date: colored rectangle full width (respecting margins), white text
    date_left_pad_mm = 1.5
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(x=margin, y=pdf.get_y(), w=avail_w_mm, h=rect_height_mm, style='F')
    pdf.set_xy(margin + date_left_pad_mm, pdf.get_y())
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(config["date_font"], size=config["date_font_size"])
    date_text = entry["dateline"]
    pdf.cell(avail_w_mm - date_left_pad_mm, rect_height_mm, date_text, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(date_gap_mm)

    # Text
    pdf.set_xy(margin, pdf.get_y())
    pdf.set_font(config["text_font"], size=config["text_font_size"])
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

    # Images
    for idx, img in enumerate(entry.get("images", [])):
        image_type = img.get("type", "png")
        image_data = img.get("image_data", "")
        pil_img = decode_base64_image(image_data, image_type)
        if pil_img:
            max_w_mm = avail_w_mm
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
    pdf.ln(GAP_BETWEEN_ENTRIES_MM)

def create_pdf_from_json(json_path, output_pdf=None, page_size="A5", date_font="3270NerdFont-Regular", date_font_size=18, text_font="WarblerText", text_font_size=12, line_spacing=1.3, margin_inch=0.35):
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
    font_path = "/Users/julian/Dropbox (Personal)/Projects By Year/@2025/OMATA Process Diary/ProcessDiaryEntries/WarblerTextV1.2-Regular.otf"
    pdf.add_font("WarblerText", "", font_path)
    date_font_path = "/Users/julian/Dropbox (Personal)/Projects By Year/@2025/OMATA Process Diary/ProcessDiaryEntries/3270NerdFont-Regular.ttf"
    pdf.add_font("3270NerdFont-Regular", "", date_font_path)
    pdf.add_page()
    with open(json_path, "r", encoding="utf-8") as f:
        diary = json.load(f)
    for entry in diary["entries"]:
        add_entry_to_pdf(pdf, entry, config)
    if not output_pdf:
        base, _ = os.path.splitext(os.path.basename(json_path))
        base = re.sub(r'\s+', '_', base)
        output_pdf = f"{base}_{page_size.upper()}.pdf"
    pdf.output(output_pdf)
    logging.info(f"Created {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="Input JSON file")
    parser.add_argument("--margin", type=float, default=0.35, help="Margin in inches (default: 0.35)")
    parser.add_argument("--page_size", type=str, default="A5", help="Page size (A4, A5, A6, etc.)")
    parser.add_argument("--date_font", type=str, default="3270NerdFont-Regular", help="Font for date line")
    parser.add_argument("--date_font_size", type=int, default=11, help="Font size for date line")
    parser.add_argument("--text_font", type=str, default="WarblerText", help="Font for text")
    parser.add_argument("--text_font_size", type=int, default=9, help="Font size for text")
    parser.add_argument("--line_spacing", type=float, default=1.2, help="Line spacing multiplier")
    args = parser.parse_args()
    create_pdf_from_json(
        args.input_json,
        None,
        page_size=args.page_size,
        date_font=args.date_font,
        date_font_size=args.date_font_size,
        text_font=args.text_font,
        text_font_size=args.text_font_size,
        line_spacing=args.line_spacing,
        margin_inch=args.margin
    )