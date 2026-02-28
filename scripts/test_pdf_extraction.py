import fitz  # PyMuPDF
from pathlib import Path

# -------- TEST PDF TEXT EXTRACTION --------
def test_pdfs():
    """
    Test text extraction from PDFs to diagnose the issue
    """
    
    books_path = Path("books")
    pdf_files = list(books_path.rglob("*.pdf"))
    
    if not pdf_files:
        print("No PDFs found!")
        return
    
    print(f"Found {len(pdf_files)} PDF files\n")
    print("="*80)
    
    # Test first 3 PDFs
    for pdf_path in pdf_files[:3]:
        print(f"\n📖 Testing: {pdf_path.name}")
        print(f"   Path: {pdf_path}")
        
        try:
            doc = fitz.open(str(pdf_path))
            print(f"   ✓ Opened successfully")
            print(f"   Pages: {len(doc)}")
            
            # Try different extraction methods
            if len(doc) > 0:
                page = doc[0]
                
                # Method 1: get_text() default
                text1 = page.get_text()
                print(f"   Method 1 get_text(): {len(text1)} chars")
                
                # Method 2: get_text("text")
                text2 = page.get_text("text")
                print(f"   Method 2 get_text('text'): {len(text2)} chars")
                
                # Method 3: get_text("blocks")
                blocks = page.get_text("blocks")
                print(f"   Method 3 get_text('blocks'): {len(blocks)} blocks")
                
                # Show preview
                if text1:
                    print(f"\n   Preview (first 300 chars):")
                    print(f"   {text1[:300]}")
                elif text2:
                    print(f"\n   Preview (first 300 chars):")
                    print(f"   {text2[:300]}")
                else:
                    print("\n   ⚠️ NO TEXT EXTRACTED - PDF might be scanned images!")
                    print(f"   ⚠️ Image-based PDFs require OCR (tesseract)")
            
            doc.close()
            print("\n" + "-"*80)
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
            print("-"*80)

if __name__ == "__main__":
    test_pdfs()
