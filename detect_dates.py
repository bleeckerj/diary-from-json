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
    stripped = line.strip()
    if not stripped:
        return False
    # Heuristic: skip lines that are only digits or too short to be a date
    if stripped.isdigit() or len(stripped) < 5:
        return False
    # Heuristic: require at least one alphabetic character (for month names, etc.)
    if not any(c.isalpha() for c in stripped):
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
            return True
    return False

def extract_date_lines(filepath):
    nlp = load_spacy_model()
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    date_lines = []
    total = len(lines)
    logging.info(f"Processing {total} lines...")
    # First, collect all date line indices, log progress every 10,000 lines
    date_indices = []
    i = 0
    while i < total:
        line = lines[i]
        if (i+1) % 10000 == 0:
            logging.info(f"Progress: processed {i+1}/{total} lines...")
        stripped = line.strip()
        # Detect start of image block
        if stripped.startswith("![](data:image/"):
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
            else:
                # Accumulate lines until closing parenthesis
                if base64_start != -1:
                    base64_data = line[base64_start+7:].strip()
                j = i + 1
                while j < total:
                    next_line = lines[j]
                    base64_data += next_line.strip()
                    if ')' in next_line:
                        image_end = j
                        break
                    j += 1
                i = image_end
            size_bytes = int(len(base64_data) * 3 / 4) if base64_data else 0
            image_snippet = base64_data[:40] + ('...' if len(base64_data) > 40 else '')
            logging.info(f"Image detected at lines {image_start+1}-{image_end+1}: type={image_type}, size~{size_bytes} bytes, snippet='{image_snippet}'")
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
    # For each date, determine the diary entry range and log summary
    logging.info(f"Starting second pass: processing {len(date_indices)} diary entries...")
    total_image_count = 0
    total_image_bytes = 0
    total_word_count = 0
    for i, date_idx in enumerate(date_indices):
        date_line = lines[date_idx].strip()
        next_date_idx = date_indices[i + 1] if i + 1 < len(date_indices) else len(lines)
        # Collect all lines (text, image, etc.) between this date and the next date
        entry_lines = []
        text_lines = []
        image_count = 0
        image_total_size = 0
        word_count = 0
        # Log every diary entry (dateline) as it is processed
        logging.info(f"Processing DIARY ENTRY {i+1}/{len(date_indices)}: dateline at line {date_idx+1}: {date_line}")
        for j in range(date_idx + 1, next_date_idx):
            content = lines[j].rstrip('\n')
            if content.strip() == "":
                continue
            if content.strip().startswith("![](data:image/"):
                image_type = None
                base64_start = content.find('base64,')
                try:
                    image_type = content.split('![](data:image/')[1].split(';')[0]
                except Exception:
                    image_type = 'unknown'
                if base64_start != -1:
                    base64_data = content[base64_start+7:].replace(')', '').strip()
                    size_bytes = int(len(base64_data) * 3 / 4)
                    image_snippet = base64_data[:40] + ('...' if len(base64_data) > 40 else '')
                    logging.info(f"    Image in diary entry: type={image_type}, size~{size_bytes} bytes, line {j+1}, snippet='{image_snippet}'")
                    image_total_size += size_bytes
                else:
                    logging.info(f"    Image in diary entry: type={image_type}, size unknown, line {j+1}, snippet='{content[:40]}...'")
                image_count += 1
                continue
            # Otherwise, treat as text
            text_lines.append(content.strip())
            word_count += len(content.strip().split())
            entry_lines.append(content)
        # Log dateline and diary entry summary
        if text_lines:
            logging.info(f"    First two lines of text: {text_lines[:2]}")
        else:
            logging.info(f"    No text lines in diary entry.")
        logging.info(f"    Number of images: {image_count}, total image size: {image_total_size} bytes")
        logging.info(f"    Number of words in text: {word_count}")
        date_lines.append((date_idx+1, date_line))
        total_image_count += image_count
        total_image_bytes += image_total_size
        total_word_count += word_count
    logging.info(f"Finished second pass: processed {len(date_indices)} diary entries.")
    logging.info(f"Finished processing {total} lines. {len(date_indices)} date-like lines found.")
    logging.info(f"SUMMARY: {len(date_indices)} diary entries, {total_image_count} images, {total_word_count} words, {total_image_bytes} image bytes.")
    return date_lines

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

    filepath = args.markdown_file
    date_lines = extract_date_lines(filepath)
    logging.info("Date-like lines detected:")
    for lineno, line in date_lines:
        logging.info(f"Date Line {lineno}: {line}")

if __name__ == "__main__":
    main()
import logging
import spacy
from dateutil import parser

