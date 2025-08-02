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