# verify_output.py
# Verify the structure of generated DATA and META files

import xlrd
import os

def verify_data_file(file_path):
    """Verify DATA file structure"""
    print(f"Verifying DATA file: {file_path}")
    print("="*70)

    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_name('DATA')

    print(f"Sheet: {sheet.name}")
    print(f"Rows: {sheet.nrows}, Columns: {sheet.ncols}")
    print()

    # Check row 0 (codes)
    print("Row 0 (Codes):")
    for col in range(min(5, sheet.ncols)):  # Show first 5 columns
        value = sheet.cell_value(0, col)
        print(f"  Col {col}: {value}")
    print("  ...")
    print()

    # Check row 1 (descriptions)
    print("Row 1 (Descriptions):")
    for col in range(min(5, sheet.ncols)):
        value = sheet.cell_value(1, col)
        print(f"  Col {col}: {value}")
    print("  ...")
    print()

    # Check row 2 (data)
    if sheet.nrows > 2:
        print("Row 2 (Data - 2024):")
        year = sheet.cell_value(2, 0)
        print(f"  Col 0 (Year): {year}")

        # Check first data value (Total Assets)
        total = sheet.cell_value(2, 1)
        print(f"  Col 1 (Total Assets): {total}")

        # Check some percentage values
        print(f"  Col 2 (CASH): {sheet.cell_value(2, 2)}")
        print(f"  Col 3 (DOMESTICEQUITYSECURITIES): {sheet.cell_value(2, 3)}")
        print("  ...")
    print()

def verify_meta_file(file_path):
    """Verify META file structure"""
    print(f"Verifying META file: {file_path}")
    print("="*70)

    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_name('META')

    print(f"Sheet: {sheet.name}")
    print(f"Rows: {sheet.nrows}, Columns: {sheet.ncols}")
    print()

    # Check header row
    print("Row 0 (Headers):")
    for col in range(min(10, sheet.ncols)):  # Show first 10 columns
        value = sheet.cell_value(0, col)
        print(f"  Col {col}: {value}")
    print("  ...")
    print()

    # Check first data row
    if sheet.nrows > 1:
        print("Row 1 (First time series metadata):")
        print(f"  CODE: {sheet.cell_value(1, 0)}")
        print(f"  DESCRIPTION: {sheet.cell_value(1, 1)}")
        print(f"  FREQUENCY: {sheet.cell_value(1, 2)}")
        print(f"  MULTIPLIER: {sheet.cell_value(1, 3)}")
    print()

def main():
    data_file = "./output/latest/CHEF_UBS_DATA_latest.xls"
    meta_file = "./output/latest/CHEF_UBS_META_latest.xls"

    if os.path.exists(data_file):
        verify_data_file(data_file)
    else:
        print(f"[ERROR] DATA file not found: {data_file}")

    print("\n")

    if os.path.exists(meta_file):
        verify_meta_file(meta_file)
    else:
        print(f"[ERROR] META file not found: {meta_file}")

    print("="*70)
    print("[OK] Verification complete")
    print("="*70)

if __name__ == '__main__':
    main()
