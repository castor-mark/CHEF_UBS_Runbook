# test_camelot_extraction.py
# Extract the Post-employment benefit plans table using Camelot

import camelot
import pandas as pd
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"
page_number = "361"  # Camelot uses 1-indexed page numbers

print(f"Opening PDF: {pdf_path}")
print(f"Extracting tables from page {page_number} using Camelot\n")

# Create output directory
os.makedirs("test_output", exist_ok=True)

# Method 1: Lattice method (for tables with visible borders/lines)
print("="*80)
print("METHOD 1: LATTICE (for tables with borders)")
print("="*80)

try:
    tables_lattice = camelot.read_pdf(
        pdf_path,
        pages=page_number,
        flavor='lattice'
    )

    print(f"Tables found: {len(tables_lattice)}")

    if len(tables_lattice) > 0:
        for i, table in enumerate(tables_lattice):
            print(f"\n--- Table {i+1} ---")
            print(f"Shape: {table.df.shape}")
            print(f"Accuracy: {table.accuracy:.2f}%")
            print(f"Whitespace: {table.whitespace:.2f}%")

            # Save to CSV
            csv_path = f"test_output/camelot_lattice_table_{i+1}.csv"
            table.df.to_csv(csv_path, index=False)
            print(f"Saved to: {csv_path}")

            # Save to text with better formatting
            txt_path = f"test_output/camelot_lattice_table_{i+1}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"CAMELOT LATTICE EXTRACTION - Table {i+1}\n")
                f.write("="*80 + "\n")
                f.write(f"Shape: {table.df.shape[0]} rows x {table.df.shape[1]} columns\n")
                f.write(f"Accuracy: {table.accuracy:.2f}%\n")
                f.write(f"Whitespace: {table.whitespace:.2f}%\n")
                f.write("="*80 + "\n\n")

                # Write table with row numbers
                for idx, row in table.df.iterrows():
                    f.write(f"Row {idx:3d}: {list(row.values)}\n")

            print(f"Saved to: {txt_path}")

            # Display first 20 rows
            print("\nFirst 20 rows:")
            print(table.df.head(20).to_string())
    else:
        print("No tables found with lattice method")

except Exception as e:
    print(f"Error with lattice method: {e}")

# Method 2: Stream method (for tables without borders)
print("\n" + "="*80)
print("METHOD 2: STREAM (for tables without borders)")
print("="*80)

try:
    tables_stream = camelot.read_pdf(
        pdf_path,
        pages=page_number,
        flavor='stream'
    )

    print(f"Tables found: {len(tables_stream)}")

    if len(tables_stream) > 0:
        for i, table in enumerate(tables_stream):
            print(f"\n--- Table {i+1} ---")
            print(f"Shape: {table.df.shape}")
            print(f"Accuracy: {table.accuracy:.2f}%")

            # Save to CSV
            csv_path = f"test_output/camelot_stream_table_{i+1}.csv"
            table.df.to_csv(csv_path, index=False)
            print(f"Saved to: {csv_path}")

            # Save to text with better formatting
            txt_path = f"test_output/camelot_stream_table_{i+1}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"CAMELOT STREAM EXTRACTION - Table {i+1}\n")
                f.write("="*80 + "\n")
                f.write(f"Shape: {table.df.shape[0]} rows x {table.df.shape[1]} columns\n")
                f.write(f"Accuracy: {table.accuracy:.2f}%\n")
                f.write("="*80 + "\n\n")

                # Write table with row numbers
                for idx, row in table.df.iterrows():
                    f.write(f"Row {idx:3d}: {list(row.values)}\n")

            print(f"Saved to: {txt_path}")

            # Display first 20 rows
            print("\nFirst 20 rows:")
            print(table.df.head(20).to_string())
    else:
        print("No tables found with stream method")

except Exception as e:
    print(f"Error with stream method: {e}")

# Method 3: Stream with edge detection
print("\n" + "="*80)
print("METHOD 3: STREAM with EDGE DETECTION")
print("="*80)

try:
    tables_stream_edge = camelot.read_pdf(
        pdf_path,
        pages=page_number,
        flavor='stream',
        edge_tol=50
    )

    print(f"Tables found: {len(tables_stream_edge)}")

    if len(tables_stream_edge) > 0:
        for i, table in enumerate(tables_stream_edge):
            print(f"\n--- Table {i+1} ---")
            print(f"Shape: {table.df.shape}")
            print(f"Accuracy: {table.accuracy:.2f}%")

            # Save to CSV
            csv_path = f"test_output/camelot_stream_edge_table_{i+1}.csv"
            table.df.to_csv(csv_path, index=False)
            print(f"Saved to: {csv_path}")

            # Save to text
            txt_path = f"test_output/camelot_stream_edge_table_{i+1}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"CAMELOT STREAM EDGE EXTRACTION - Table {i+1}\n")
                f.write("="*80 + "\n")
                f.write(f"Shape: {table.df.shape[0]} rows x {table.df.shape[1]} columns\n")
                f.write(f"Accuracy: {table.accuracy:.2f}%\n")
                f.write("="*80 + "\n\n")

                for idx, row in table.df.iterrows():
                    f.write(f"Row {idx:3d}: {list(row.values)}\n")

            print(f"Saved to: {txt_path}")

            print("\nFirst 20 rows:")
            print(table.df.head(20).to_string())
    else:
        print("No tables found with stream edge method")

except Exception as e:
    print(f"Error with stream edge method: {e}")

print("\n" + "="*80)
print("[OK] CAMELOT EXTRACTION COMPLETE")
print("="*80)
print("\nCheck 'test_output' directory for:")
print("  - CSV files for easy viewing in Excel")
print("  - TXT files for structure analysis")
