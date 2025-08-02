import { OmataDiarySchema } from "./schema";
import * as fs from "fs";
import * as path from "path";

// Change this to your JSON file path
const jsonFile = process.argv[2] || "OMATA-NOTES  Year 5  Day 2 (Week 209).json";

const data = JSON.parse(fs.readFileSync(path.resolve(jsonFile), "utf-8"));

try {
  OmataDiarySchema.parse(data);
  console.log("✅ JSON conforms to schema.");
} catch (e) {
  console.error("❌ JSON does NOT conform to schema.");
  if (e instanceof Error) {
    console.error(e.message);
  }
}