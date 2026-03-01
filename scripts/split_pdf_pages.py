import fitz  # PyMuPDF
import json

pdf_path = "American Revolution.pdf"

# Open PDF
doc = fitz.open(pdf_path)

pages = {}

# Extract text page by page
for page_index in range(len(doc)):
    page = doc[page_index]
    text = page.get_text("text")
    pages[page_index + 1] = text

print("Total pages extracted:", len(pages))

# Preview first page
print("\n--- Page 1 Preview ---\n")
print(pages[1][:1000])

# Save pages to JSON
with open("american_revolution_pages.json", "w", encoding="utf-8") as f:
    json.dump(pages, f, indent=2, ensure_ascii=False)

print("\nPages saved to american_revolution_pages.json")
