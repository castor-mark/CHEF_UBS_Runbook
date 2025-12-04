# test_parser_csv.py
# Test parser that extracts data from Camelot CSV for BOTH years
# Focus: Identify bolded headers and extract allocation percentages correctly

import camelot
import pandas as pd
import os

pdf_path = "downloads/20251202_152313/2024/Annual_Report_UBS_Group_2024.pdf"
page_number = "361"

print("="*80)
print("UBS TABLE EXTRACTION TEST - BOTH YEARS")
print("="*80)
print()

# Extract table using Camelot
print("Extracting table with Camelot...")
tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream')

if len(tables) == 0:
    print("[ERROR] No tables found")
    exit(1)

df = tables[0].df
print(f"[OK] Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"[OK] Accuracy: {tables[0].accuracy:.2f}%")
print()

# Save CSV for reference
os.makedirs("test_output", exist_ok=True)
csv_path = "test_output/test_extraction.csv"
df.to_csv(csv_path, index=False)
print(f"[OK] Saved to: {csv_path}")
print()

print("="*80)
print("PARSING TABLE - EXTRACTING BOTH 2024 AND 2023 DATA")
print("="*80)
print()

# Column indices
COL_ASSET_NAME = 0
COL_2024_PERCENT = 4  # 31.12.24 Allocation %
COL_2024_TOTAL = 3    # 31.12.24 Total fair value
COL_2023_PERCENT = 8  # 31.12.23 Allocation %
COL_2023_TOTAL = 7    # 31.12.23 Total fair value

def clean_number(value_str):
    """Clean and convert string to number"""
    if value_str is None or value_str == '' or str(value_str).lower() == 'nan':
        return None

    cleaned = str(value_str).replace(' ', '').replace(',', '').replace('\xa0', '').strip()

    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]

    try:
        return float(cleaned)
    except ValueError:
        return None

# Initialize data structure for BOTH years
data_2024 = {
    'year': '2024',
    'total_assets': None,
    'percentages': {}
}

data_2023 = {
    'year': '2023',
    'total_assets': None,
    'percentages': {}
}

# Skip header rows (rows 0-5)
print("Starting from row 6 (after headers)...")
print()

# Track current section/subsection
current_section = None
current_subsection = None

# Process each row
for idx, row in df.iterrows():
    if idx < 6:  # Skip header rows
        continue

    asset_name = str(row[COL_ASSET_NAME]).strip()

    if not asset_name or asset_name == '' or asset_name == 'nan':
        continue

    # Get percentages for BOTH years
    pct_2024_raw = str(row[COL_2024_PERCENT]).strip()
    pct_2024 = clean_number(pct_2024_raw)

    pct_2023_raw = str(row[COL_2023_PERCENT]).strip()
    pct_2023 = clean_number(pct_2023_raw)

    # Get total fair values for BOTH years
    total_2024_raw = str(row[COL_2024_TOTAL]).strip()
    total_2024 = clean_number(total_2024_raw)

    total_2023_raw = str(row[COL_2023_TOTAL]).strip()
    total_2023 = clean_number(total_2023_raw)

    asset_lower = asset_name.lower()

    # Check if this is a SECTION HEADER (bolded in PDF)
    # Section headers have NO percentage values
    is_section_header = (pct_2024 is None or pct_2024 == 0) and (pct_2023 is None or pct_2023 == 0) and \
                       (total_2024 is None or total_2024 == 0) and (total_2023 is None or total_2023 == 0)

    print(f"Row {idx:3d}: {asset_name}")
    print(f"         2024%: {pct_2024}, 2023%: {pct_2023}")
    print(f"         Section header: {is_section_header}")

    # Special rows - Total assets
    if 'total fair value of plan assets' in asset_lower:
        if total_2024 is not None and total_2024 > 10000:
            data_2024['total_assets'] = total_2024
            print(f"         >>> TOTAL ASSETS 2024: {total_2024}")

        if total_2023 is not None and total_2023 > 10000:
            data_2023['total_assets'] = total_2023
            print(f"         >>> TOTAL ASSETS 2023: {total_2023}")
        print()
        continue

    # Special rows - Other investments
    if 'other investments' in asset_lower:
        if pct_2024 is not None:
            data_2024['percentages']['OTHERINVESTMENTS'] = pct_2024
            print(f"         >>> OTHERINVESTMENTS 2024: {pct_2024}%")

        if pct_2023 is not None:
            data_2023['percentages']['OTHERINVESTMENTS'] = pct_2023
            print(f"         >>> OTHERINVESTMENTS 2023: {pct_2023}%")
        print()
        continue

    # SECTION 1: Cash and cash equivalents
    if 'cash and cash equivalents' in asset_lower:
        if pct_2024 is not None:
            data_2024['percentages']['CASH'] = pct_2024
            print(f"         >>> CASH 2024: {pct_2024}%")

        if pct_2023 is not None:
            data_2023['percentages']['CASH'] = pct_2023
            print(f"         >>> CASH 2023: {pct_2023}%")
        print()

    # SECTION 2: Equity securities (MAIN SECTION - for aggregated EQUITIES)
    elif asset_lower == 'equity securities':
        current_section = 'EQUITY_SECURITIES'
        print(f"         >>> SECTION: Equity securities")
        print()

    elif current_section == 'EQUITY_SECURITIES':
        if 'domestic' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICEQUITYSECURITIES'] = pct_2024
                print(f"         >>> DOMESTICEQUITYSECURITIES 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICEQUITYSECURITIES'] = pct_2023
                print(f"         >>> DOMESTICEQUITYSECURITIES 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNEQUITYSECURITIES'] = pct_2024
                print(f"         >>> FOREIGNEQUITYSECURITIES 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNEQUITYSECURITIES'] = pct_2023
                print(f"         >>> FOREIGNEQUITYSECURITIES 2023: {pct_2023}%")
            current_section = None
            print()

    # SECTION 3: Bonds (MAIN SECTION - for aggregated BONDS)
    elif asset_lower == 'bonds':
        current_section = 'BONDS'
        print(f"         >>> SECTION: Bonds")
        print()

    elif current_section == 'BONDS':
        if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['NONINVESTDOMESTICBONDS'] = pct_2024
                print(f"         >>> NONINVESTDOMESTICBONDS 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['NONINVESTDOMESTICBONDS'] = pct_2023
                print(f"         >>> NONINVESTDOMESTICBONDS 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['NONINVESTFOREIGNBONDSRATED'] = pct_2024
                print(f"         >>> NONINVESTFOREIGNBONDSRATED 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['NONINVESTFOREIGNBONDSRATED'] = pct_2023
                print(f"         >>> NONINVESTFOREIGNBONDSRATED 2023: {pct_2023}%")
            current_section = None
            print()

    # SECTION 4: Real estate / property (MAIN SECTION - for aggregated REALESTATE)
    elif 'real estate' in asset_lower and 'property' in asset_lower:
        current_section = 'REALESTATE'
        print(f"         >>> SECTION: Real estate / property")
        print()

    elif current_section == 'REALESTATE':
        if 'domestic' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICREALESTATE'] = pct_2024
                print(f"         >>> DOMESTICREALESTATE 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICREALESTATE'] = pct_2023
                print(f"         >>> DOMESTICREALESTATE 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNREALESTATE'] = pct_2024
                print(f"         >>> FOREIGNREALESTATE 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNREALESTATE'] = pct_2023
                print(f"         >>> FOREIGNREALESTATE 2023: {pct_2023}%")
            current_section = None
            print()

    # SECTION 5: Investment funds (with subsections)
    elif 'investment funds' in asset_lower:
        current_section = 'INVESTMENT_FUNDS'
        print(f"         >>> SECTION: Investment funds")
        print()

    # Investment funds SUBSECTIONS - check BEFORE main section
    elif current_subsection == 'INV_EQUITY':
        if 'domestic' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICEQUITIES'] = pct_2024
                print(f"         >>> DOMESTICEQUITIES 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICEQUITIES'] = pct_2023
                print(f"         >>> DOMESTICEQUITIES 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNEQUITIES'] = pct_2024
                print(f"         >>> FOREIGNEQUITIES 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNEQUITIES'] = pct_2023
                print(f"         >>> FOREIGNEQUITIES 2023: {pct_2023}%")
            current_subsection = None
            print()

    elif current_subsection == 'INV_BONDS':
        if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICBONDS'] = pct_2024
                print(f"         >>> DOMESTICBONDS 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICBONDS'] = pct_2023
                print(f"         >>> DOMESTICBONDS 2023: {pct_2023}%")
            print()

        elif 'domestic' in asset_lower and 'below bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICBONDSJUNK'] = pct_2024
                print(f"         >>> DOMESTICBONDSJUNK 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICBONDSJUNK'] = pct_2023
                print(f"         >>> DOMESTICBONDSJUNK 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNBONDSRATED'] = pct_2024
                print(f"         >>> FOREIGNBONDSRATED 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNBONDSRATED'] = pct_2023
                print(f"         >>> FOREIGNBONDSRATED 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower and 'below bbb' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNBONDSJUNK'] = pct_2024
                print(f"         >>> FOREIGNBONDSJUNK 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNBONDSJUNK'] = pct_2023
                print(f"         >>> FOREIGNBONDSJUNK 2023: {pct_2023}%")
            current_subsection = None
            print()

    elif current_subsection == 'INV_REALESTATE':
        if 'domestic' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['DOMESTICREALESTATEINVESTMENTS'] = pct_2024
                print(f"         >>> DOMESTICREALESTATEINVESTMENTS 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['DOMESTICREALESTATEINVESTMENTS'] = pct_2023
                print(f"         >>> DOMESTICREALESTATEINVESTMENTS 2023: {pct_2023}%")
            print()

        elif 'foreign' in asset_lower:
            if pct_2024 is not None:
                data_2024['percentages']['FOREIGNREALESTATEINVESTMENTS'] = pct_2024
                print(f"         >>> FOREIGNREALESTATEINVESTMENTS 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['FOREIGNREALESTATEINVESTMENTS'] = pct_2023
                print(f"         >>> FOREIGNREALESTATEINVESTMENTS 2023: {pct_2023}%")
            current_subsection = None
            print()

    # Investment funds main section - detect subsections
    elif current_section == 'INVESTMENT_FUNDS':
        if asset_lower == 'equity':
            current_subsection = 'INV_EQUITY'
            print(f"         >>> SUBSECTION: Investment funds > Equity")
            print()

        elif asset_lower.startswith('bonds'):
            current_subsection = 'INV_BONDS'
            print(f"         >>> SUBSECTION: Investment funds > Bonds")
            print()

        elif asset_lower == 'real estate':
            current_subsection = 'INV_REALESTATE'
            print(f"         >>> SUBSECTION: Investment funds > Real estate")
            print()

        elif asset_lower == 'other':
            if pct_2024 is not None:
                data_2024['percentages']['OTHER'] = pct_2024
                print(f"         >>> OTHER 2024: {pct_2024}%")

            if pct_2023 is not None:
                data_2023['percentages']['OTHER'] = pct_2023
                print(f"         >>> OTHER 2023: {pct_2023}%")
            print()

# Calculate aggregated percentages (ONLY from main sections)
print()
print("="*80)
print("CALCULATING AGGREGATED PERCENTAGES")
print("="*80)
print()

# 2024 aggregated
bonds_2024 = data_2024['percentages'].get('NONINVESTDOMESTICBONDS', 0) + \
             data_2024['percentages'].get('NONINVESTFOREIGNBONDSRATED', 0)

equities_2024 = data_2024['percentages'].get('DOMESTICEQUITYSECURITIES', 0) + \
                data_2024['percentages'].get('FOREIGNEQUITYSECURITIES', 0)

realestate_2024 = data_2024['percentages'].get('DOMESTICREALESTATE', 0) + \
                  data_2024['percentages'].get('FOREIGNREALESTATE', 0)

data_2024['percentages']['BONDS'] = bonds_2024
data_2024['percentages']['EQUITIES'] = equities_2024
data_2024['percentages']['REALESTATE'] = realestate_2024

print(f"2024 Aggregated:")
print(f"  BONDS = NONINVESTDOMESTICBONDS + NONINVESTFOREIGNBONDSRATED = {bonds_2024}%")
print(f"  EQUITIES = DOMESTICEQUITYSECURITIES + FOREIGNEQUITYSECURITIES = {equities_2024}%")
print(f"  REALESTATE = DOMESTICREALESTATE + FOREIGNREALESTATE = {realestate_2024}%")
print()

# 2023 aggregated
bonds_2023 = data_2023['percentages'].get('NONINVESTDOMESTICBONDS', 0) + \
             data_2023['percentages'].get('NONINVESTFOREIGNBONDSRATED', 0)

equities_2023 = data_2023['percentages'].get('DOMESTICEQUITYSECURITIES', 0) + \
                data_2023['percentages'].get('FOREIGNEQUITYSECURITIES', 0)

realestate_2023 = data_2023['percentages'].get('DOMESTICREALESTATE', 0) + \
                  data_2023['percentages'].get('FOREIGNREALESTATE', 0)

data_2023['percentages']['BONDS'] = bonds_2023
data_2023['percentages']['EQUITIES'] = equities_2023
data_2023['percentages']['REALESTATE'] = realestate_2023

print(f"2023 Aggregated:")
print(f"  BONDS = NONINVESTDOMESTICBONDS + NONINVESTFOREIGNBONDSRATED = {bonds_2023}%")
print(f"  EQUITIES = DOMESTICEQUITYSECURITIES + FOREIGNEQUITYSECURITIES = {equities_2023}%")
print(f"  REALESTATE = DOMESTICREALESTATE + FOREIGNREALESTATE = {realestate_2023}%")
print()

# Final summary
print("="*80)
print("EXTRACTION SUMMARY")
print("="*80)
print()

print("2024 DATA:")
print(f"  Year: {data_2024['year']}")
print(f"  Total Assets: {data_2024['total_assets']} USD millions")
print(f"  Asset Classes: {len(data_2024['percentages'])}")
print()

print("2023 DATA:")
print(f"  Year: {data_2023['year']}")
print(f"  Total Assets: {data_2023['total_assets']} USD millions")
print(f"  Asset Classes: {len(data_2023['percentages'])}")
print()

# Validation - sum of individual percentages (excluding aggregated)
individual_2024 = [
    'CASH', 'DOMESTICEQUITYSECURITIES', 'FOREIGNEQUITYSECURITIES',
    'NONINVESTDOMESTICBONDS', 'NONINVESTFOREIGNBONDSRATED',
    'DOMESTICREALESTATE', 'FOREIGNREALESTATE',
    'DOMESTICEQUITIES', 'FOREIGNEQUITIES',
    'DOMESTICBONDS', 'DOMESTICBONDSJUNK',
    'FOREIGNBONDSRATED', 'FOREIGNBONDSJUNK',
    'DOMESTICREALESTATEINVESTMENTS', 'FOREIGNREALESTATEINVESTMENTS',
    'OTHER', 'OTHERINVESTMENTS'
]

total_2024 = sum([data_2024['percentages'].get(key, 0) for key in individual_2024])
total_2023 = sum([data_2023['percentages'].get(key, 0) for key in individual_2024])

print(f"2024 Percentage Total: {total_2024}% (deviation: {abs(100 - total_2024)}%)")
print(f"2023 Percentage Total: {total_2023}% (deviation: {abs(100 - total_2023)}%)")
print()

print("="*80)
print("[OK] TEST COMPLETE")
print("="*80)
