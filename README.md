# OMATA Diary Conversion Utilities

This project provides utilities for converting free-form markdown diary documents into structured JSON and print-ready PDF formats.  
It is designed to help organize, preserve, and prepare your OMATA startup diary for book or archival presentation.

---

## Requirements

- Python 3.8+
- [fpdf2](https://pypi.org/project/fpdf2/)
- [Pillow](https://pypi.org/project/Pillow/)
- Fonts used in your diary (e.g., WarblerText, 3270NerdFont-Regular, DejaVuSans)
- Any additional requirements listed in your `requirements.txt`

Install dependencies:

```sh
pip install fpdf2 Pillow
```

---

## diary_json2pdf.py

Converts a structured JSON diary (output from `process_omata_diary.py`) into a print-ready PDF.

### Usage

```sh
python diary_json2pdf.py <input_json> [options]
```

### Command Line Arguments

- `input_json` (positional): Path to the input JSON file.
- `--margin`: Margin in inches (default: 0.35)
- `--page_size`: Page size (A4, A5, A6, etc.; default: A5)
- `--date_font`: Font for date line (default: 3270NerdFont-Regular)
- `--date_font_size`: Font size for date line (default: 11)
- `--text_font`: Font for text (default: WarblerText)
- `--text_font_size`: Font size for text (default: 9)
- `--line_spacing`: Line spacing multiplier (default: 1)
- `--rect_corner_radius_mm`: Corner radius for left corners of date rectangle in millimeters (default: 2)
- `--rect_fill_color`: Fill color for date rectangle as three RGB values, e.g. `--rect_fill_color 30 30 30`

### Output

- The output PDF filename is generated from the input JSON filename, with spaces replaced by underscores and the page size appended, e.g.:
  ```
  OMATA-NOTES__Continued_At_Week_182_A5.pdf
  ```

### Functionality

- Renders each diary entry with a colored date rectangle, text, and images.
- Prevents orphaned datelines at page breaks.
- Scales images to fit the page width.
- Respects specified margins and page size.

---

## process_omata_diary.py

Converts unstructured markdown diary files into structured JSON.

### Functionality

- Reads markdown files containing diary entries, images, tables, and other media.
- Extracts dates, text, images, and metadata for each entry.
- Uses AI (if enabled/configured) to infer structure and categorize content.
- Outputs a JSON file with fields for date, text, images, and other metadata.

### Usage

```sh
python process_omata_diary.py <input_markdown> [options]
```

### Options

- See script help (`python process_omata_diary.py --help`) for available arguments.

### Output

- Structured JSON file suitable for use with `diary_json2pdf.py`.

---

## Example Workflow

1. **Convert Markdown to JSON:**
   ```sh
   python process_omata_diary.py OMATA-NOTES.md
   ```
   Output: `OMATA-NOTES.json`

2. **Convert JSON to PDF:**
   ```sh
   python diary_json2pdf.py OMATA-NOTES.json --page_size A5 --margin 0.5 --date_font_size 14 --text_font_size 10
   ```
   Output: `OMATA-NOTES_A5.pdf`

---

## Notes

- Ensure your fonts are available and paths are correct.
- For best results, review the JSON output before generating the PDF.
- The utilities are modular and can be extended for additional diary features.

## JSON Schema
```
import { z } from "zod";

const DiaryTextLineSchema = z.object({
  text: z.string(),
  line: z.number(),
  filename: z.string(),
});

const DiaryImageSchema = z.object({
  type: z.string(),
  image_data: z.string(),
  line_start: z.number(),
  line_end: z.number(),
  size_bytes: z.number(),
  filename: z.string(),
});

const DiaryEntrySchema = z.object({
  dateline: z.string(),
  dateline_line: z.number(),
  filename: z.string(),
  text: z.array(DiaryTextLineSchema),
  images: z.array(DiaryImageSchema),
});

const MetadataSchema = z.object({
  num_entries: z.number(),
  line_range: z.tuple([z.number(), z.number()]),
  total_images: z.number(),
  total_words: z.number(),
  total_image_bytes: z.number(),
  first_entry: z.string().nullable(),
  last_entry: z.string().nullable(),
});

export const OmataDiarySchema = z.object({
  metadata: MetadataSchema,
  entries: z.array(DiaryEntrySchema),
});
```