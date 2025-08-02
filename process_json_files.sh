#!/bin/bash

# List of input files
FILES=(

  "OMATA-NOTES__Continued_At_Week_202.json"

)
#   "OMATA-NOTES__Continued_At_Week_182.json"
#   "OMATA-NOTES_START_XYZ_Weeks_of_a_Hardware_Startup.json"
#   "OMATA-NOTES_Year_5_Day_2_Week_209.json"
# Run for A5
source .venv/bin/activate

for f in "${FILES[@]}"; do
  python3 ./diary_json2pdf.py "$f" --page_size A5 --text_font_size 11 --date_font_size 11 --rect_fill_color 100 30 30
done

# Run for A6
for f in "${FILES[@]}"; do
  python3 ./diary_json2pdf.py "$f" --page_size A6 --text_font_size 9 --date_font_size 9 --rect_fill_color 100 30 30
done