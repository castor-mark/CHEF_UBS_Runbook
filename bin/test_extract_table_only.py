# test_extract_table_only.py
# Simple script to extract the full table as CSV using Camelot
# NO PARSING - just extraction and display

import camelot
import pandas as pd
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"
page_number = "361"

print("="*80)
print("TABLE EXTRACTION ONLY - NO PARSING")
print("="*80)
print()

# Extract table using Camelot stream method
print(f"Extracting table from page {page_number} using Camelot...")
tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream')

if len(tables) == 0:
    print("[ERROR] No tables found")
    exit(1)

df = tables[0].df
print(f"[OK] Extracted table:")
print(f"     Rows: {df.shape[0]}")
print(f"     Columns: {df.shape[1]}")
print(f"     Accuracy: {tables[0].accuracy:.2f}%")
print()

# Save to CSV
os.makedirs("test_output", exist_ok=True)
csv_path = "test_output/extracted_table.csv"
df.to_csv(csv_path, index=False)
print(f"[OK] Saved to: {csv_path}")
print()

# Display the full table structure
print("="*80)
print("FULL TABLE STRUCTURE")
print("="*80)
print()

# Show column headers
print("Column structure:")
for col_idx in range(df.shape[1]):
    print(f"  Column {col_idx}")
print()

# Show ALL rows with row numbers
print("All rows (with row numbers):")
print("-"*80)
for idx, row in df.iterrows():
    print(f"Row {idx:3d}: ", end="")
    # Show first 4 columns (asset name and first 3 data columns)
    for col_idx in range(min(4, df.shape[1])):
        cell_value = str(row[col_idx]).strip()
        if cell_value == 'nan' or cell_value == '':
            cell_value = '[empty]'
        print(f"[{col_idx}:{cell_value[:20]:20s}] ", end="")
    print()
print()

# Save to text file with full structure
txt_path = "test_output/extracted_table_structure.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("FULL TABLE EXTRACTION\n")
    f.write("="*80 + "\n\n")
    f.write(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")
    f.write(f"Accuracy: {tables[0].accuracy:.2f}%\n")
    f.write("="*80 + "\n\n")

    # Write all rows with ALL columns
    for idx, row in df.iterrows():
        f.write(f"Row {idx:3d}:\n")
        for col_idx in range(df.shape[1]):
            cell_value = str(row[col_idx]).strip()
            f.write(f"  Col {col_idx}: {cell_value}\n")
        f.write("\n")

print(f"[OK] Full structure saved to: {txt_path}")
print()

print("="*80)
print("[OK] EXTRACTION COMPLETE")
print("="*80)
print()
print("Next step: Analyze the CSV structure to identify:")
print("  1. Header rows (rows 0-5)")
print("  2. Data rows (rows 6+)")
print("  3. Column 4 = 2024 allocation %")
print("  4. Column 8 = 2023 allocation %")
print()
print("Files created:")
print(f"  - {csv_path}")
print(f"  - {txt_path}")
