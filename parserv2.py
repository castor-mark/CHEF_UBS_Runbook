# parserv2.py
# Intelligent PDF Parser for UBS Annual Reports
# NO HARD CODING - Dynamic table detection and parsing

import pdfplumber
import camelot
import pandas as pd
import os
import json
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class UBSPDFParserV2:
    """Extracts post-employment benefit plan data from UBS Annual Report PDFs"""

    def __init__(self):
        self.debug = config.DEBUG_MODE
        self.logger = logger

    def extract_year_from_pdf(self, pdf_path):
        """
        Extract the report year from PDF filename or content.
        Priority: filename -> PDF content
        """
        # Try filename first
        import os
        filename = os.path.basename(pdf_path)
        import re
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
            self.logger.info(f"Extracted year from filename: {year}")
            return year

        # Try PDF content
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    match = re.search(r'Annual Report\s+(\d{4})', text)
                    if match:
                        year = match.group(1)
                        self.logger.info(f"Extracted year from PDF content: {year}")
                        return year
        except Exception as e:
            self.logger.error(f"Error extracting year: {e}")

        return None

    def find_benefit_plans_page(self, pdf_path):
        """
        Find the page containing "Post-employment benefit plans" table.
        Searches BACKWARDS from end (financial tables usually near end).
        Returns page number (1-indexed for Camelot).
        """
        self.logger.info("Searching for Post-employment benefit plans section...")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"Total pages: {total_pages}, searching backwards from end...")

                # Search backwards (financial tables are usually near the end)
                for page_num in range(total_pages - 1, -1, -1):
                    page = pdf.pages[page_num]
                    text = page.extract_text()

                    if not text:
                        continue

                    text_lower = text.lower()

                    # More specific keywords for faster matching
                    # Look for the specific table we need - SWISS defined benefit plans
                    # FLEXIBLE: Handle variations like "Swiss" or "Switzerland"
                    if "composition and fair value" in text_lower:
                        # Must be Swiss table (not UK table)
                        # Check multiple variations
                        if "swiss" in text_lower or "switzerland" in text_lower:
                            # Check if it's the benefit plans table
                            for keyword in config.PDF_TABLE_KEYWORDS:
                                if keyword.lower() in text_lower:
                                    # Also check for date markers to confirm it's the right table
                                    if "31.12." in text:
                                        # Return 1-indexed page number for Camelot
                                        self.logger.info(f"Found benefit plans table on page {page_num + 1}")
                                        return str(page_num + 1)

        except Exception as e:
            self.logger.error(f"Error finding benefit plans section: {e}")

        return None

    def extract_table_with_camelot(self, pdf_path, page_number, output_dir, year):
        """
        Extract the benefit plans table using Camelot and save to CSV.
        Uses edge_tol=500 to capture full table including date headers.
        Returns tuple: (DataFrame, CSV path, metadata)
        """
        self.logger.info(f"Extracting table from page {page_number} using Camelot...")

        try:
            # Use stream method with edge_tol=500 to capture full table including date headers
            tables = camelot.read_pdf(
                pdf_path,
                pages=page_number,
                flavor='stream',
                edge_tol=500
            )

            if len(tables) == 0:
                self.logger.error("No tables found by Camelot")
                return None, None, None

            # Get the first table
            table = tables[0]
            df = table.df

            self.logger.info(f"Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
            self.logger.info(f"Table accuracy: {table.accuracy:.2f}%")

            # Create output directory: extracted/TIMESTAMP/YEAR/
            timestamp = config.RUN_TIMESTAMP
            extract_dir = os.path.join("extracted", timestamp, year)
            os.makedirs(extract_dir, exist_ok=True)

            # Save CSV
            csv_filename = f"benefit_plans_table_{year}.csv"
            csv_path = os.path.join(extract_dir, csv_filename)
            df.to_csv(csv_path, index=False)
            self.logger.info(f"Saved extracted table to: {csv_path}")

            # Create metadata
            metadata = {
                'extraction_timestamp': timestamp,
                'pdf_file': os.path.basename(pdf_path),
                'page_number': int(page_number),
                'table_shape': list(df.shape),
                'camelot_accuracy': float(table.accuracy),
                'year': year
            }

            # Save metadata
            metadata_path = os.path.join(extract_dir, f"extraction_metadata_{year}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            self.logger.info(f"Saved extraction metadata to: {metadata_path}")

            return df, csv_path, metadata

        except Exception as e:
            self.logger.error(f"Error extracting table with Camelot: {e}")
            return None, None, None

    def auto_detect_allocation_offset(self, df, date_col, date_row):
        """
        Auto-detect the correct column offset for allocation %.
        Tries +1, +2, +3 and validates by checking if column contains 'allocation %'.
        Returns the correct offset or None if not found.
        """
        import re

        # Search in header rows (date_row and nearby rows) for "allocation %" text
        for offset in [1, 2, 3]:
            test_col = date_col + offset
            if test_col >= df.shape[1]:
                continue

            # Check a few rows around date_row for "allocation" keyword
            for check_row in range(max(0, date_row - 2), min(df.shape[0], date_row + 5)):
                cell_value = str(df.iloc[check_row, test_col]).strip().lower()
                if 'allocation' in cell_value and '%' in cell_value:
                    self.logger.info(f"Auto-detected allocation % column at offset +{offset} (col {test_col})")
                    return offset

        # Fallback: Default to +2 (most common pattern)
        self.logger.warning(f"Could not auto-detect allocation column, using default offset +2")
        return 2

    def find_date_columns(self, df):
        """
        Dynamically find which columns contain which year's data.
        AUTO-DETECTS the correct column offset for allocation % (handles +1, +2, or +3).
        Pattern: Date at col N → Allocation % at col N+offset
        Returns dict with year info.
        """
        self.logger.info("Searching for date columns...")

        date_info = {}
        detected_offset = None

        for idx, row in df.iterrows():
            for col_idx in range(df.shape[1]):
                cell_value = str(row[col_idx]).strip()

                # Look for date patterns (31.12.XX)
                import re
                date_match = re.search(r'31\.12\.(\d{2})', cell_value)
                if date_match:
                    year_short = date_match.group(1)
                    year_full = f"20{year_short}"

                    # Auto-detect offset on first date found
                    if detected_offset is None:
                        detected_offset = self.auto_detect_allocation_offset(df, col_idx, idx)

                    # Calculate allocation column using detected offset
                    allocation_col = col_idx + detected_offset

                    if 'year1' not in date_info:
                        date_info['year1'] = {
                            'year': year_full,
                            'col': allocation_col,
                            'date': cell_value,
                            'row': idx,
                            'date_col': col_idx
                        }
                        self.logger.info(f"Found Year 1: {year_full} at Date Col {col_idx}, Allocation Col {allocation_col} (offset +{detected_offset})")
                    elif 'year2' not in date_info:
                        date_info['year2'] = {
                            'year': year_full,
                            'col': allocation_col,
                            'date': cell_value,
                            'row': idx,
                            'date_col': col_idx
                        }
                        self.logger.info(f"Found Year 2: {year_full} at Date Col {col_idx}, Allocation Col {allocation_col} (offset +{detected_offset})")
                        break

            if 'year1' in date_info and 'year2' in date_info:
                break

        # Store detected offset for validation
        if date_info:
            date_info['detected_offset'] = detected_offset

        return date_info

    def find_data_bounds(self, df):
        """
        Dynamically find where data starts and ends.
        Returns tuple: (first_data_row, last_data_row)
        """
        self.logger.info("Finding data boundaries...")

        first_row = None
        last_row = None

        for idx, row in df.iterrows():
            asset_name = str(row[0]).strip().lower()

            # Find first data row (Cash)
            if first_row is None and 'cash and cash equiv' in asset_name:
                first_row = idx
                self.logger.info(f"First data row (Cash) at row {idx}")

            # Find last data row (Total fair value)
            if 'total fair value of plan assets' in asset_name:
                last_row = idx
                self.logger.info(f"Last data row (Total) at row {idx}")
                break

        return first_row, last_row

    def clean_number(self, value_str):
        """Clean and convert a string to a number"""
        if value_str is None or value_str == '' or str(value_str).lower() == 'nan':
            return None

        cleaned = str(value_str).replace(' ', '').replace(',', '').replace('\xa0', '').strip()

        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_table_data(self, df, date_info, first_row, last_row):
        """
        Parse the table and extract data for BOTH years.
        Returns list with 2 records: [year1_data, year2_data]
        """
        self.logger.info("Parsing table data...")

        # Get column indices for each year
        year1_col = date_info['year1']['col']
        year2_col = date_info['year2']['col']

        # Initialize data structures for BOTH years
        data_year1 = {
            'year': date_info['year1']['year'],
            'total_assets': None,
            'percentages': {}
        }

        data_year2 = {
            'year': date_info['year2']['year'],
            'total_assets': None,
            'percentages': {}
        }

        # Track current section/subsection
        current_section = None
        current_subsection = None

        # Process data rows
        for idx in range(first_row, last_row + 1):
            row = df.iloc[idx]
            asset_name = str(row[0]).strip()

            if not asset_name or asset_name == 'nan':
                continue

            asset_lower = asset_name.lower()

            # Get values for BOTH years
            pct_year1 = self.clean_number(str(row[year1_col]).strip())
            pct_year2 = self.clean_number(str(row[year2_col]).strip())

            # Get total fair value (column before allocation %)
            total_year1 = self.clean_number(str(row[year1_col - 1]).strip())
            total_year2 = self.clean_number(str(row[year2_col - 1]).strip())

            self.logger.debug(f"Row {idx}: {asset_name} | Y1: {pct_year1}% | Y2: {pct_year2}%")

            # Check for special rows
            if 'total fair value of plan assets' in asset_lower:
                if total_year1 is not None and total_year1 > 10000:
                    data_year1['total_assets'] = total_year1
                if total_year2 is not None and total_year2 > 10000:
                    data_year2['total_assets'] = total_year2
                continue

            if 'other investments' in asset_lower:
                if pct_year1 is not None:
                    data_year1['percentages']['OTHERINVESTMENTS'] = pct_year1
                if pct_year2 is not None:
                    data_year2['percentages']['OTHERINVESTMENTS'] = pct_year2
                continue

            # Parse asset categories
            if 'cash and cash equiv' in asset_lower:
                if pct_year1 is not None:
                    data_year1['percentages']['CASH'] = pct_year1
                if pct_year2 is not None:
                    data_year2['percentages']['CASH'] = pct_year2

            elif asset_lower == 'equity securities':
                current_section = 'EQUITY_SECURITIES'

            elif current_section == 'EQUITY_SECURITIES':
                if 'domestic' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICEQUITYSECURITIES'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICEQUITYSECURITIES'] = pct_year2
                elif 'foreign' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNEQUITYSECURITIES'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNEQUITYSECURITIES'] = pct_year2
                    current_section = None

            elif asset_lower == 'bonds':
                current_section = 'BONDS'

            elif current_section == 'BONDS':
                if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['NONINVESTDOMESTICBONDS'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['NONINVESTDOMESTICBONDS'] = pct_year2
                elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['NONINVESTFOREIGNBONDSRATED'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['NONINVESTFOREIGNBONDSRATED'] = pct_year2
                    current_section = None

            elif 'real estate' in asset_lower and 'property' in asset_lower:
                current_section = 'REALESTATE'

            elif current_section == 'REALESTATE':
                if 'domestic' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICREALESTATE'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICREALESTATE'] = pct_year2
                elif 'foreign' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNREALESTATE'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNREALESTATE'] = pct_year2
                    current_section = None

            elif 'investment funds' in asset_lower:
                current_section = 'INVESTMENT_FUNDS'

            # Investment funds subsections (check BEFORE main section)
            elif current_subsection == 'INV_EQUITY':
                if 'domestic' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICEQUITIES'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICEQUITIES'] = pct_year2
                elif 'foreign' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNEQUITIES'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNEQUITIES'] = pct_year2
                    current_subsection = None

            elif current_subsection == 'INV_BONDS':
                if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICBONDS'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICBONDS'] = pct_year2
                elif 'domestic' in asset_lower and 'below bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICBONDSJUNK'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICBONDSJUNK'] = pct_year2
                elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNBONDSRATED'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNBONDSRATED'] = pct_year2
                elif 'foreign' in asset_lower and 'below bbb' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNBONDSJUNK'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNBONDSJUNK'] = pct_year2
                    current_subsection = None

            elif current_subsection == 'INV_REALESTATE':
                if 'domestic' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['DOMESTICREALESTATEINVESTMENTS'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['DOMESTICREALESTATEINVESTMENTS'] = pct_year2
                elif 'foreign' in asset_lower:
                    if pct_year1 is not None:
                        data_year1['percentages']['FOREIGNREALESTATEINVESTMENTS'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['FOREIGNREALESTATEINVESTMENTS'] = pct_year2
                    current_subsection = None

            elif current_section == 'INVESTMENT_FUNDS':
                if asset_lower == 'equity':
                    current_subsection = 'INV_EQUITY'
                elif asset_lower.startswith('bonds'):
                    current_subsection = 'INV_BONDS'
                elif asset_lower == 'real estate':
                    current_subsection = 'INV_REALESTATE'
                elif asset_lower == 'other':
                    if pct_year1 is not None:
                        data_year1['percentages']['OTHER'] = pct_year1
                    if pct_year2 is not None:
                        data_year2['percentages']['OTHER'] = pct_year2

        return [data_year1, data_year2]

    def calculate_aggregated_percentages(self, percentages):
        """
        Calculate aggregated percentages ONLY from main sections.
        BONDS = main Bonds section only (NOT Investment funds bonds)
        EQUITIES = main Equity securities only (NOT Investment funds equity)
        REALESTATE = main Real estate/property only (NOT Investment funds real estate)
        """
        # Calculate BONDS (ONLY main section)
        bonds_total = sum([
            percentages.get('NONINVESTDOMESTICBONDS', 0),
            percentages.get('NONINVESTFOREIGNBONDSRATED', 0)
        ])

        # Calculate EQUITIES (ONLY main section)
        equities_total = sum([
            percentages.get('DOMESTICEQUITYSECURITIES', 0),
            percentages.get('FOREIGNEQUITYSECURITIES', 0)
        ])

        # Calculate REALESTATE (ONLY main section)
        realestate_total = sum([
            percentages.get('DOMESTICREALESTATE', 0),
            percentages.get('FOREIGNREALESTATE', 0)
        ])

        percentages['BONDS'] = bonds_total
        percentages['EQUITIES'] = equities_total
        percentages['REALESTATE'] = realestate_total

        self.logger.info(f"Calculated aggregated percentages - Bonds: {bonds_total}%, Equities: {equities_total}%, Real Estate: {realestate_total}%")

        return percentages

    def validate_extracted_data(self, data_list):
        """
        Comprehensive validation of extracted data.
        Checks for common issues and provides detailed warnings.
        Returns: (is_valid, warnings_list)
        """
        warnings = []
        is_valid = True

        for data in data_list:
            year = data.get('year', 'Unknown')
            percentages = data.get('percentages', {})
            total_assets = data.get('total_assets', 0)

            # Validation 1: Check percentage total
            total_pct = sum([v for k, v in percentages.items() if k not in ['BONDS', 'EQUITIES', 'REALESTATE']])
            if abs(total_pct - 100) > 2:  # Allow 2% tolerance
                warnings.append(f"{year}: Percentage total is {total_pct}% (expected ~100%)")
                is_valid = False
                self.logger.warning(f"{year}: Percentage validation failed: {total_pct}%")
            else:
                self.logger.info(f"{year} Percentage validation passed: {total_pct}%")

            # Validation 2: Check total assets is reasonable
            if total_assets < 1000 or total_assets > 1000000:  # USD millions
                warnings.append(f"{year}: Total assets {total_assets}M seems unusual (expected 1,000-1,000,000M)")
                self.logger.warning(f"{year}: Total assets {total_assets}M seems unusual")

            # Validation 3: Check we have key asset classes
            required_classes = ['CASH', 'DOMESTICEQUITYSECURITIES', 'FOREIGNEQUITYSECURITIES']
            missing = [cls for cls in required_classes if cls not in percentages]
            if missing:
                warnings.append(f"{year}: Missing required asset classes: {missing}")
                self.logger.warning(f"{year}: Missing asset classes: {missing}")

            # Validation 4: Check aggregated values exist
            if 'BONDS' not in percentages or 'EQUITIES' not in percentages or 'REALESTATE' not in percentages:
                warnings.append(f"{year}: Missing aggregated percentages")
                is_valid = False
                self.logger.error(f"{year}: Aggregated percentages not calculated")

        return is_valid, warnings

    def parse_pdf(self, pdf_path):
        """
        Main method to parse a PDF report.
        Returns list with 2 dicts (one for each year).
        """
        self.logger.info(f"\nParsing PDF: {pdf_path}")

        # Step 1: Extract year
        year = self.extract_year_from_pdf(pdf_path)
        if not year:
            self.logger.error("Could not extract year from PDF")
            return None

        # Step 2: Find benefit plans page
        page_number = self.find_benefit_plans_page(pdf_path)
        if page_number is None:
            self.logger.error("Could not find benefit plans table")
            return None

        # Step 3: Extract table with Camelot and save to CSV
        df, csv_path, metadata = self.extract_table_with_camelot(pdf_path, page_number, "extracted", year)
        if df is None:
            self.logger.error("Could not extract table with Camelot")
            return None

        # Step 4: Find date columns dynamically
        date_info = self.find_date_columns(df)
        if not date_info or 'year1' not in date_info or 'year2' not in date_info:
            self.logger.error("Could not find date columns")
            return None

        # Update metadata with dates found
        metadata['dates_found'] = [date_info['year1']['date'], date_info['year2']['date']]
        metadata['years'] = [date_info['year1']['year'], date_info['year2']['year']]

        # Step 5: Find data boundaries
        first_row, last_row = self.find_data_bounds(df)
        if first_row is None or last_row is None:
            self.logger.error("Could not find data boundaries")
            return None

        # Step 6: Parse table data for BOTH years
        parsed_data = self.parse_table_data(df, date_info, first_row, last_row)

        # Step 7: Calculate aggregated percentages for both years
        for data in parsed_data:
            data['percentages'] = self.calculate_aggregated_percentages(data['percentages'])

        # Step 8: Validation
        if config.VALIDATE_PERCENTAGE_TOTAL:
            for data in parsed_data:
                base_percentages = [
                    'CASH', 'DOMESTICEQUITYSECURITIES', 'FOREIGNEQUITYSECURITIES',
                    'NONINVESTDOMESTICBONDS', 'NONINVESTFOREIGNBONDSRATED',
                    'DOMESTICREALESTATE', 'FOREIGNREALESTATE',
                    'DOMESTICEQUITIES', 'FOREIGNEQUITIES',
                    'DOMESTICBONDS', 'DOMESTICBONDSJUNK',
                    'FOREIGNBONDSRATED', 'FOREIGNBONDSJUNK',
                    'DOMESTICREALESTATEINVESTMENTS', 'FOREIGNREALESTATEINVESTMENTS',
                    'OTHER', 'OTHERINVESTMENTS'
                ]

                total_pct = sum([data['percentages'].get(key, 0) for key in base_percentages])
                deviation = abs(total_pct - 100.0)

                if deviation > config.PERCENTAGE_TOLERANCE:
                    self.logger.warning(f"{data['year']} Percentage total: {total_pct}% (deviation: {deviation}%)")
                else:
                    self.logger.info(f"{data['year']} Percentage validation passed: {total_pct}%")

        # Step 9: Comprehensive validation
        is_valid, warnings = self.validate_extracted_data(parsed_data)
        if not is_valid:
            self.logger.error("Validation failed! Issues detected:")
            for warning in warnings:
                self.logger.error(f"  - {warning}")
        elif warnings:
            self.logger.warning("Validation passed with warnings:")
            for warning in warnings:
                self.logger.warning(f"  - {warning}")

        self.logger.info(f"Successfully parsed - {len(parsed_data)} years extracted")
        for data in parsed_data:
            self.logger.info(f"  {data['year']}: Total Assets: {data['total_assets']}, Asset Classes: {len(data['percentages'])}")

        return parsed_data


def main():
    """Test the parser with a sample PDF"""
    import sys
    from logger_setup import setup_logging

    setup_logging()

    if len(sys.argv) < 2:
        print("Usage: python parserv2.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    parser = UBSPDFParserV2()
    results = parser.parse_pdf(pdf_file)

    if results:
        print("\n" + "="*80)
        print("EXTRACTION RESULTS")
        print("="*80)

        for data in results:
            print(f"\nYear: {data['year']}")
            print(f"Total Assets: {data['total_assets']} USD millions")
            print(f"\nAsset Allocation Percentages:")

            for asset_code, percentage in sorted(data['percentages'].items()):
                print(f"  {asset_code}: {percentage}%")


if __name__ == '__main__':
    main()
