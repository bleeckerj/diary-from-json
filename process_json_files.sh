#!/bin/bash

# List of input files
FILES=(


  "DiaryEntriesFromBear/ListOfThingsNeverDone.json"
  "DiaryEntriesFromBear/OMATA-NOTES__Continued_At_Week_202.json"
   "DiaryEntriesFromBear/OMATA-NOTES__Continued_At_Week_182.json"
   "DiaryEntriesFromBear/OMATA-NOTES_START_XYZ_Weeks_of_a_Hardware_Startup.json"
   "DiaryEntriesFromBear/OMATA-NOTES_Year_5_Day_2_Week_209.json"
)


# Run for A5
source .venv/bin/activate

# for f in "${FILES[@]}"; do
#   python3 ./diary_json2pdf.py "$f" --page_size A5 --text_font_size 11 --date_font_size 11 --rect_fill_color 40 40 60 --text_font "nyt-cheltenham-normal" --date_font "imperial-italic-600"
# done

# Run for A6
for f in "${FILES[@]}"; do
  python3 ./diary_json2pdf.py "$f" --page_size POCKET --text_font_size 10 --date_font_size 9.5 --rect_fill_color 40 40 60 --text_font "nyt-cheltenham-normal" --date_font "imperial-italic-600"
done