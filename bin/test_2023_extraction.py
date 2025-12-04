# test_2023_extraction.py
# Test extraction on 2023 PDF to verify NO HARD CODING approach works

import camelot
import pandas as pd
import os

# 2023 PDF
pdf_path = "Project_information/annual-report-ubs-group-2023.pdf"
page_number = "392"

print("="*100)
print("2023 PDF EXTRACTION TEST")
print("="*100)
print()

# Extract table using Camelot
print(f"Extracting from: {pdf_path}")
print(f"Page: {page_number}")
print()

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
csv_path = "test_output/2023_table.csv"
df.to_csv(csv_path, index=False)
print(f"[OK] Saved to: {csv_path}")
print()

# Find dates dynamically (NO HARD CODING!)
print("="*100)
print("FINDING DATE COLUMNS (NO HARD CODING)")
print("="*100)
print()

date_cols = {}
for idx, row in df.iterrows():
    for col_idx in range(df.shape[1]):
        cell_value = str(row[col_idx]).strip()

        # Look for date patterns
        if '31.12.23' in cell_value or '2023' in cell_value and '31.12' in cell_value:
            if 'year1' not in date_cols:
                date_cols['year1'] = {'col': col_idx, 'date': cell_value, 'row': idx}
                print(f"[FOUND] Year 1: Row {idx}, Col {col_idx} = {cell_value}")

        if '31.12.22' in cell_value or '2022' in cell_value and '31.12' in cell_value:
            if 'year2' not in date_cols:
                date_cols['year2'] = {'col': col_idx, 'date': cell_value, 'row': idx}
                print(f"[FOUND] Year 2: Row {idx}, Col {col_idx} = {cell_value}")

print()

# Show header structure
print("="*100)
print("TABLE HEADER STRUCTURE")
print("="*100)
print()

for idx in range(min(6, df.shape[0])):
    print(f"Row {idx}:")
    for col_idx in range(df.shape[1]):
        cell_value = str(df.iloc[idx, col_idx]).strip()
        if cell_value == 'nan' or cell_value == '':
            cell_value = '[empty]'
        print(f"  Col {col_idx}: {cell_value}")
    print()

# Show first few data rows
print("="*100)
print("FIRST DATA ROWS")
print("="*100)
print()

# Find Cash row (first data row)
cash_row = None
for idx, row in df.iterrows():
    cell_value = str(row[0]).strip().lower()
    if 'cash and cash equiv' in cell_value:
        cash_row = idx
        break

if cash_row:
    print(f"[FOUND] First data row (Cash) at row {cash_row}")
    print()

    # Show Cash row and next 3 rows
    for idx in range(cash_row, min(cash_row + 4, df.shape[0])):
        print(f"Row {idx}:")
        for col_idx in range(df.shape[1]):
            cell_value = str(df.iloc[idx, col_idx]).strip()
            if cell_value == 'nan' or cell_value == '':
                cell_value = '[empty]'
            print(f"  Col {col_idx}: {cell_value}")
        print()

# Show date row
print("="*100)
print("DATE ROW")
print("="*100)
print()

if date_cols:
    date_row = date_cols.get('year1', {}).get('row')
    if date_row is not None:
        print(f"Row {date_row} (Date identifiers):")
        for col_idx in range(df.shape[1]):
            cell_value = str(df.iloc[date_row, col_idx]).strip()
            if cell_value == 'nan' or cell_value == '':
                cell_value = '[empty]'
            print(f"  Col {col_idx}: {cell_value}")
        print()

print("="*100)
print("[OK] 2023 EXTRACTION COMPLETE")
print("="*100)
print()
print(f"CSV saved to: {csv_path}")
print("Compare this structure with 2024 to verify consistency!")
