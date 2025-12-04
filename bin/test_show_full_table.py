# test_show_full_table.py
# Display the FULL table structure exactly as extracted - NO HARD CODING

import camelot
import pandas as pd
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"
page_number = "361"

print("="*100)
print("FULL TABLE EXTRACTION - EXACT STRUCTURE")
print("="*100)
print()

# Extract table using Camelot
print(f"Extracting from page {page_number}...")
tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream')

if len(tables) == 0:
    print("[ERROR] No tables found")
    exit(1)

df = tables[0].df
print(f"[OK] Extracted: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"[OK] Accuracy: {tables[0].accuracy:.2f}%")
print()

# Save CSV
os.makedirs("test_output", exist_ok=True)
csv_path = "test_output/full_table.csv"
df.to_csv(csv_path, index=False)
print(f"[OK] Saved to: {csv_path}")
print()

# Display FULL table with ALL columns
print("="*100)
print("FULL TABLE - ALL ROWS AND COLUMNS")
print("="*100)
print()

# Show each row with ALL column values
for idx, row in df.iterrows():
    print(f"Row {idx:3d}:")
    for col_idx in range(df.shape[1]):
        cell_value = str(row[col_idx]).strip()
        if cell_value == 'nan' or cell_value == '':
            cell_value = '[empty]'
        print(f"  Col {col_idx}: {cell_value}")
    print()

print("="*100)
print("[OK] COMPLETE")
print("="*100)
