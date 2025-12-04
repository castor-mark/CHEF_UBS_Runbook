# test_full_table_extraction.py
# Test different Camelot parameters to extract FULL table including date headers

import camelot
import pandas as pd
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"
page_number = "361"

print("="*100)
print("TESTING FULL TABLE EXTRACTION - INCLUDING DATE HEADERS")
print("="*100)
print()

os.makedirs("test_output", exist_ok=True)

# Test 1: Stream with default settings (current method)
print("Test 1: Stream flavor (default)")
print("-"*100)
try:
    tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream')
    if tables:
        df = tables[0].df
        print(f"Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {tables[0].accuracy:.2f}%")
        print(f"First 3 rows:")
        for i in range(min(3, len(df))):
            print(f"  Row {i}: {list(df.iloc[i][:5])}")
        df.to_csv("test_output/test1_stream_default.csv", index=False)
        print(f"Saved to: test_output/test1_stream_default.csv")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 2: Stream with edge_tol (detect table edges better)
print("Test 2: Stream flavor with edge_tol=500")
print("-"*100)
try:
    tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream', edge_tol=500)
    if tables:
        df = tables[0].df
        print(f"Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {tables[0].accuracy:.2f}%")
        print(f"First 3 rows:")
        for i in range(min(3, len(df))):
            print(f"  Row {i}: {list(df.iloc[i][:5])}")
        df.to_csv("test_output/test2_stream_edge500.csv", index=False)
        print(f"Saved to: test_output/test2_stream_edge500.csv")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 3: Stream with row_tol (merge rows closer together)
print("Test 3: Stream flavor with row_tol=15")
print("-"*100)
try:
    tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream', row_tol=15)
    if tables:
        df = tables[0].df
        print(f"Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {tables[0].accuracy:.2f}%")
        print(f"First 3 rows:")
        for i in range(min(3, len(df))):
            print(f"  Row {i}: {list(df.iloc[i][:5])}")
        df.to_csv("test_output/test3_stream_rowtol15.csv", index=False)
        print(f"Saved to: test_output/test3_stream_rowtol15.csv")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 4: Lattice flavor (for tables with lines/borders)
print("Test 4: Lattice flavor")
print("-"*100)
try:
    tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='lattice')
    if tables:
        df = tables[0].df
        print(f"Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {tables[0].accuracy:.2f}%")
        print(f"First 3 rows:")
        for i in range(min(3, len(df))):
            print(f"  Row {i}: {list(df.iloc[i][:5])}")
        df.to_csv("test_output/test4_lattice.csv", index=False)
        print(f"Saved to: test_output/test4_lattice.csv")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 5: Stream with multiple tables (maybe dates are in separate table)
print("Test 5: Stream flavor - extract ALL tables")
print("-"*100)
try:
    tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream')
    print(f"Found {len(tables)} table(s)")
    for idx, table in enumerate(tables):
        df = table.df
        print(f"\nTable {idx + 1}:")
        print(f"  Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {table.accuracy:.2f}%")
        print(f"  First row: {list(df.iloc[0][:5])}")
        df.to_csv(f"test_output/test5_table{idx+1}.csv", index=False)
        print(f"  Saved to: test_output/test5_table{idx+1}.csv")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 6: Stream with table_areas (specify exact table region)
# We'll try to capture a larger area to include headers
print("Test 6: Stream with expanded table_areas")
print("-"*100)
try:
    # Try to capture larger area (adjust coordinates to include headers)
    # Format: x1,y1,x2,y2 (left,top,right,bottom)
    tables = camelot.read_pdf(
        pdf_path,
        pages=page_number,
        flavor='stream',
        table_areas=['50,700,550,100']  # Expanded vertical range
    )
    if tables:
        df = tables[0].df
        print(f"Rows: {df.shape[0]}, Cols: {df.shape[1]}, Accuracy: {tables[0].accuracy:.2f}%")
        print(f"First 5 rows:")
        for i in range(min(5, len(df))):
            print(f"  Row {i}: {list(df.iloc[i][:5])}")
        df.to_csv("test_output/test6_stream_expanded.csv", index=False)
        print(f"Saved to: test_output/test6_stream_expanded.csv")
except Exception as e:
    print(f"Error: {e}")
print()

print("="*100)
print("ANALYSIS: Check which test captured the date headers (31.12.24, 31.12.23)")
print("="*100)
print()

# Search for dates in each extracted CSV
for test_num in range(1, 7):
    csv_file = f"test_output/test{test_num}_*.csv"
    import glob
    files = glob.glob(csv_file)

    for file in files:
        if os.path.exists(file):
            print(f"Checking {os.path.basename(file)}:")
            df = pd.read_csv(file)

            # Look for dates in first 5 rows
            found_dates = False
            for idx in range(min(5, len(df))):
                for col in df.columns:
                    cell = str(df.iloc[idx][col])
                    if '31.12.' in cell:
                        print(f"  [FOUND] Date '{cell}' at row {idx}, col {col}")
                        found_dates = True

            if not found_dates:
                print(f"  [NO DATES] Date headers not found in first 5 rows")
            print()

print("="*100)
print("[COMPLETE] Check test_output/ folder for all extracted CSVs")
print("="*100)
