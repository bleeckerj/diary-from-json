# OMATA Process Diary Conversion Utility

This project converts free-form markdown diary documents into structured JSON, and then generates print-ready PDFs from those JSON files. The diary entries include text, dates, images, tables, and other media, and are intended to help organize and present the experience of running the OMATA startup.

## Features

- Extracts dates, text, images, and metadata from markdown files.
- Converts unstructured diary entries into structured JSON.
- Generates print-ready PDFs with customizable fonts, colors, page sizes, and rounded rectangles.
- Supports custom fonts and AI-enabled content inference (future functionality).

## Usage

### Convert Markdown to JSON

```bash
python3 diary_markdown2json.py input.md [options]
```

### Convert JSON to PDF

```bash
python3 diary_json2pdf.py input.json [options]
```

### Command Line Arguments

#### `diary_markdown2json.py`
- `input.md` (positional): Path to the markdown file to process.
- `--log`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO

#### `diary_json2pdf.py`
- `input_json` (positional): Path to the input JSON file.
- `--margin`: Margin in inches (default: 0.35)
- `--page_size`: Page size (A4, A5, A6, POCKET, etc.; default: A5)
- `--date_font`: Font for date line (default: 3270NerdFont-Regular)
- `--date_font_size`: Font size for date line (default: 11)
- `--text_font`: Font for text (default: WarblerText)
- `--text_font_size`: Font size for text (default: 9)
- `--line_spacing`: Line spacing multiplier (default: 1.2)
- `--rect_corner_radius_mm`: Corner radius for left corners of date rectangle in millimeters (default: 1)
- `--rect_fill_color`: Fill color for date rectangle as three RGB values, e.g. `--rect_fill_color 30 30 30`

### Example

```bash
python3 diary_markdown2json.py DiaryEntriesFromBear/OMATA-NOTES__Continued_At_Week_182.md
python3 diary_json2pdf.py DiaryEntriesFromBear/OMATA-NOTES__Continued_At_Week_182.json \
  --page_size A5 \
  --text_font_size 11 \
  --date_font_size 11 \
  --rect_fill_color 40 40 60 \
  --text_font nyt-cheltenham-normal \
  --date_font imperial-italic-600 \
  --rect_corner_radius_mm 2
```

### Output

- The generated JSON will be saved alongside the input markdown file.
- The generated PDF will be saved in the same directory as the input JSON file, with a name like `OMATA-NOTES__Continued_At_Week_182_A5.pdf`.

## Fonts

Custom fonts must be registered with FPDF using their alias (not the filename). For example, use `"nyt-cheltenham-normal"` as the font name, not `"nyt-cheltenham-normal.ttf"`.

## Project Context

This utility is designed to help organize and present the OMATA startup diary for future book publication. It extracts and structures diary entries, including dates, text, images, and other media, into a format suitable for high-quality print output.

## Coding Guidelines

- Modular and well-organized code.
- Clear comments for complex logic.
- Meaningful variable and function names.
- Unit tests for critical functionality.

## Functionality Requirements

- Reads markdown files and extracts structured data.
- Determines date, text, images, and metadata for each entry.
- Outputs a structured JSON file for further processing.
- AI-enabled inference for content categorization (future implementation).