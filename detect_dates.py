import logging
import spacy
from dateutil import parser

# Load spaCy English model
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        logging.error("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
        exit(1)

def is_date_line(line, nlp):
    """
    Returns True if the line is likely to be a date line.
    Uses spaCy NER and dateutil.parser for robustness.
    """
    import re
    stripped = line.strip()
    if not stripped:
        return False
    # Heuristic: skip lines that are only digits or too short to be a date
    if stripped.isdigit() or len(stripped) < 5:
        return False
    # Heuristic: require at least one alphabetic character (for month names, etc.)
    if not any(c.isalpha() for c in stripped):
        return False
    # Reject likely base64 (long, no spaces, mostly alphanum + /+=)
    if len(stripped) > 30 and " " not in stripped:
        if re.fullmatch(r"[A-Za-z0-9+/=]+", stripped):
            return False
    # Try parsing with dateutil
    try:
        dt = parser.parse(stripped, fuzzy=False, default=None)
        return True
    except Exception:
        pass
    # Use spaCy NER
    doc = nlp(stripped)
    for ent in doc.ents:
        if ent.label_ == "DATE" and ent.text == stripped:
            # Additional check: require at least one digit or month name in the string
            if re.search(r"\d", stripped) or re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", stripped, re.IGNORECASE):
                return True
    return False

def extract_date_lines(filepath):
    nlp = load_spacy_model()
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    import json
    diary_entries = []
    total = len(lines)
    logging.info(f"Processing {total} lines...")
    # First, collect all date line indices, log progress every 10,000 lines
    date_indices = []
    import re
    i = 0
    inside_image_block = False
    image_start = None
    image_type = None
    base64_data = ''
    image_end = None
    while i < total:
        line = lines[i]
        stripped = line.strip()
        if (i+1) % 10000 == 0:
            logging.info(f"Progress: processed {i+1}/{total} lines...")
        # Detect start of image block
        if not inside_image_block and stripped.startswith("![](data:image/"):
            logging.info(f"Semantic element detected: IMAGE at line {i+1}")
            image_type = None
            base64_start = line.find('base64,')
            try:
                image_type = line.split('![](data:image/')[1].split(';')[0]
            except Exception:
                image_type = 'unknown'
                logging.warning(f"Failed to parse image type at line {i+1}: {line.strip()}")
            image_start = i
            image_end = i
            base64_data = ''
            # Check if image ends on this line
            if ')' in line:
                base64_data = line[base64_start+7:line.find(')')].strip() if base64_start != -1 else ''
                image_end = i
                size_bytes = int(len(base64_data) * 3 / 4) if base64_data else 0
                image_snippet = base64_data[:40] + ('...' if len(base64_data) > 40 else '')
                logging.info(f"Image detected at lines {image_start+1}-{image_end+1}: type={image_type}, size~{size_bytes} bytes, snippet='{image_snippet}'")
                i += 1
                continue
            else:
                # Start accumulating image block
                if base64_start != -1:
                    base64_data = line[base64_start+7:].strip()
                inside_image_block = True
                image_end = i
                i += 1
                continue
        elif inside_image_block:
            # Accumulate base64 lines until closing parenthesis
            base64_data += stripped
            if ')' in line:
                image_end = i
                size_bytes = int(len(base64_data) * 3 / 4) if base64_data else 0
                image_snippet = base64_data[:40] + ('...' if len(base64_data) > 40 else '')
                logging.info(f"Image detected at lines {image_start+1}-{image_end+1}: type={image_type}, size~{size_bytes} bytes, snippet='{image_snippet}'")
                inside_image_block = False
                image_start = None
                image_type = None
                base64_data = ''
                image_end = None
                i += 1
                continue
            else:
                i += 1
                continue
        # Only run date detection on non-image lines
        if is_date_line(line, nlp):
            logging.info(f"Semantic element detected: DATELINE at line {i+1}")
            logging.info(f"Date detected at line {i+1}: {line.strip()}")
            # Log the next line for debugging/robustness
            if i+1 < total:
                next_line = lines[i+1].strip()
                logging.info(f"  Next line after dateline: {next_line}")
            else:
                logging.info(f"  No next line after dateline (end of file)")
            date_indices.append(i)
        i += 1

    logging.info(f"Starting second pass: processing {len(date_indices)} diary entries...")
    total_image_count = 0
    total_image_bytes = 0
    total_word_count = 0
    for i, date_idx in enumerate(date_indices):
        date_line = lines[date_idx].strip()
        next_date_idx = date_indices[i + 1] if i + 1 < len(date_indices) else len(lines)
        entry_text_lines = []
        images = []
        image_count = 0
        image_total_size = 0
        word_count = 0
        # Log every diary entry (dateline) as it is processed
        logging.info(f"Processing DIARY ENTRY {i+1}/{len(date_indices)}: dateline at line {date_idx+1}: {date_line}")
        j = date_idx + 1
        while j < next_date_idx:
            content = lines[j].rstrip('\n')
            if content.strip() == "":
                j += 1
                continue
            # Handle inline images: split line at ![](data:image/
            img_marker = "![](data:image/"
            if img_marker in content:
                img_start_idx = content.find(img_marker)
                text_part = content[:img_start_idx].strip()
                image_part = content[img_start_idx:]
                # Add text before image (if any)
                if text_part:
                    entry_text_lines.append({
                        "text": text_part,
                        "line": j + 1,
                        "filename": filepath
                    })
                    word_count += len(text_part.split())
                # Now process image block
                image_type = None
                base64_start = image_part.find('base64,')
                try:
                    image_type = image_part.split('![](data:image/')[1].split(';')[0]
                except Exception:
                    image_type = 'unknown'
                image_start = j
                image_end = j
                image_data = image_part
                # If image is multi-line, accumulate until closing parenthesis
                if ')' not in image_part:
                    k = j + 1
                    while k < next_date_idx:
                        next_line = lines[k].rstrip('\n')
                        image_data += '\n' + next_line
                        if ')' in next_line:
                            image_end = k
                            break
                        k += 1
                    j = image_end
                size_bytes = int(len(image_data) * 3 / 4) if base64_start != -1 else 0
                images.append({
                    "type": image_type,
                    "image_data": image_data,
                    "line_start": image_start + 1,
                    "line_end": image_end + 1,
                    "size_bytes": size_bytes,
                    "filename": filepath
                })
                image_count += 1
                image_total_size += size_bytes
                j += 1
                continue
            # Otherwise, treat as text (skip image blocks)
            entry_text_lines.append({
                "text": content.strip(),
                "line": j + 1,
                "filename": filepath
            })
            word_count += len(content.strip().split())
            j += 1
        diary_entries.append({
            "dateline": date_line,
            "dateline_line": date_idx + 1,
            "filename": filepath,
            "text": entry_text_lines,
            "images": images
        })
        total_image_count += image_count
        total_image_bytes += image_total_size
        total_word_count += word_count
    logging.info(f"Finished second pass: processed {len(date_indices)} diary entries.")
    logging.info(f"Finished processing {total} lines. {len(date_indices)} date-like lines found.")
    logging.info(f"SUMMARY: {len(date_indices)} diary entries, {total_image_count} images, {total_word_count} words, {total_image_bytes} image bytes.")
    return diary_entries

def main():
    import argparse
    parser_ = argparse.ArgumentParser(description="Detect date-like lines in a markdown file using spaCy.")
    parser_.add_argument("markdown_file", help="Path to the markdown file to process.")
    parser_.add_argument("--log", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser_.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log.upper(), None),
        format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s'
    )

    import os
    filepath = args.markdown_file
    output_json = os.path.splitext(filepath)[0] + '.json'
    diary_entries = extract_date_lines(filepath)
    # Compute metadata
    total_entries = len(diary_entries)
    total_lines = 0
    total_images = 0
    total_words = 0
    total_image_bytes = 0
    line_min = None
    line_max = None
    for entry in diary_entries:
        if entry["text"]:
            for t in entry["text"]:
                line_num = t["line"]
                if line_min is None or line_num < line_min:
                    line_min = line_num
                if line_max is None or line_num > line_max:
                    line_max = line_num
                total_lines += 1
                total_words += len(t["text"].split())
        if entry["images"]:
            for img in entry["images"]:
                total_images += 1
                total_image_bytes += img.get("size_bytes", 0)
                if line_min is None or img["line_start"] < line_min:
                    line_min = img["line_start"]
                if line_max is None or img["line_end"] > line_max:
                    line_max = img["line_end"]
    first_entry = diary_entries[0]["dateline"] if diary_entries else None
    last_entry = diary_entries[-1]["dateline"] if diary_entries else None
    metadata = {
        "num_entries": total_entries,
        "line_range": [line_min, line_max],
        "total_images": total_images,
        "total_words": total_words,
        "total_image_bytes": total_image_bytes,
        "first_entry": first_entry,
        "last_entry": last_entry
    }
    output = {
        "metadata": metadata,
        "entries": diary_entries
    }
    logging.info(f"Metadata: {metadata}")
    # Write to JSON file
    logging.info(f"Writing structured diary entries to {output_json}")
    import json
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logging.info(f"Wrote structured diary entries to {output_json}")

if __name__ == "__main__":
    main()
import logging
import spacy
from dateutil import parser

