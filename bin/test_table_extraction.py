# test_table_extraction.py
# Extract the Post-employment benefit plans table and save structure to txt

import pdfplumber
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"

# Keywords to search for
keywords = [
    "Post-employment benefit plans (continued)",
    "Composition and fair value of Swiss defined benefit plan assets"
]

print(f"Opening PDF: {pdf_path}")
print(f"Searching for table using keywords: {keywords}\n")

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")

    # Search for the page with our keywords
    target_page = None

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()

        if text:
            # Check if all keywords are present
            if all(keyword.lower() in text.lower() for keyword in keywords):
                target_page = page_num
                print(f"[OK] Found table on page {page_num + 1}")
                break

    if target_page is None:
        print("[ERROR] Table not found!")
        exit(1)

    # Extract from the target page
    page = pdf.pages[target_page]

    # Create output directory
    os.makedirs("test_output", exist_ok=True)

    # 1. Save the full page text
    text = page.extract_text()
    with open("test_output/page_text.txt", "w", encoding="utf-8") as f:
        f.write(f"PAGE {target_page + 1} TEXT\n")
        f.write("="*80 + "\n\n")
        f.write(text)

    print(f"[OK] Saved page text to: test_output/page_text.txt")

    # 2. Try different table extraction methods

    # Method 1: Default extraction
    print("\n--- Method 1: Default table extraction ---")
    tables = page.extract_tables()
    print(f"Tables found: {len(tables)}")

    if tables:
        with open("test_output/table_default.txt", "w", encoding="utf-8") as f:
            f.write(f"DEFAULT TABLE EXTRACTION - Page {target_page + 1}\n")
            f.write("="*80 + "\n\n")

            for table_idx, table in enumerate(tables):
                f.write(f"\nTABLE {table_idx + 1}\n")
                f.write(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}\n")
                f.write("-"*80 + "\n")

                for row_idx, row in enumerate(table):
                    f.write(f"Row {row_idx:3d}: {row}\n")

        print(f"[OK] Saved to: test_output/table_default.txt")

    # Method 2: Extract with explicit lines strategy
    print("\n--- Method 2: Lines-based extraction ---")
    tables_lines = page.extract_tables(table_settings={
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    })
    print(f"Tables found: {len(tables_lines)}")

    if tables_lines:
        with open("test_output/table_lines.txt", "w", encoding="utf-8") as f:
            f.write(f"LINES-BASED TABLE EXTRACTION - Page {target_page + 1}\n")
            f.write("="*80 + "\n\n")

            for table_idx, table in enumerate(tables_lines):
                f.write(f"\nTABLE {table_idx + 1}\n")
                f.write(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}\n")
                f.write("-"*80 + "\n")

                for row_idx, row in enumerate(table):
                    f.write(f"Row {row_idx:3d}: {row}\n")

        print(f"[OK] Saved to: test_output/table_lines.txt")

    # Method 3: Extract with text strategy (for tables without borders)
    print("\n--- Method 3: Text-based extraction ---")
    tables_text = page.extract_tables(table_settings={
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
    })
    print(f"Tables found: {len(tables_text)}")

    if tables_text:
        with open("test_output/table_text.txt", "w", encoding="utf-8") as f:
            f.write(f"TEXT-BASED TABLE EXTRACTION - Page {target_page + 1}\n")
            f.write("="*80 + "\n\n")

            for table_idx, table in enumerate(tables_text):
                f.write(f"\nTABLE {table_idx + 1}\n")
                f.write(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}\n")
                f.write("-"*80 + "\n")

                for row_idx, row in enumerate(table):
                    f.write(f"Row {row_idx:3d}: {row}\n")

        print(f"[OK] Saved to: test_output/table_text.txt")

    # Method 4: Try with explicit grid detection
    print("\n--- Method 4: Explicit grid extraction ---")
    tables_explicit = page.extract_tables(table_settings={
        "vertical_strategy": "explicit",
        "horizontal_strategy": "explicit",
        "explicit_vertical_lines": page.curves + page.edges,
        "explicit_horizontal_lines": page.curves + page.edges,
    })
    print(f"Tables found: {len(tables_explicit)}")

    if tables_explicit:
        with open("test_output/table_explicit.txt", "w", encoding="utf-8") as f:
            f.write(f"EXPLICIT GRID TABLE EXTRACTION - Page {target_page + 1}\n")
            f.write("="*80 + "\n\n")

            for table_idx, table in enumerate(tables_explicit):
                f.write(f"\nTABLE {table_idx + 1}\n")
                f.write(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}\n")
                f.write("-"*80 + "\n")

                for row_idx, row in enumerate(table):
                    f.write(f"Row {row_idx:3d}: {row}\n")

        print(f"[OK] Saved to: test_output/table_explicit.txt")

    # 5. Also save page metadata for debugging
    with open("test_output/page_metadata.txt", "w", encoding="utf-8") as f:
        f.write(f"PAGE {target_page + 1} METADATA\n")
        f.write("="*80 + "\n\n")
        f.write(f"Width: {page.width}\n")
        f.write(f"Height: {page.height}\n")
        f.write(f"Number of curves: {len(page.curves)}\n")
        f.write(f"Number of edges: {len(page.edges)}\n")
        f.write(f"Number of lines: {len(page.lines)}\n")
        f.write(f"Number of rects: {len(page.rects)}\n")

    print(f"[OK] Saved metadata to: test_output/page_metadata.txt")

    print("\n" + "="*80)
    print("[OK] EXTRACTION COMPLETE")
    print("="*80)
    print("\nOutput files created in 'test_output' directory:")
    print("  - page_text.txt       : Full page text")
    print("  - table_default.txt   : Default extraction")
    print("  - table_lines.txt     : Lines-based extraction")
    print("  - table_text.txt      : Text-based extraction")
    print("  - table_explicit.txt  : Explicit grid extraction")
    print("  - page_metadata.txt   : Page metadata")
    print("\nReview these files to understand the table structure.")
