# parser.py
# Parse "Post-employment benefit plans" table from UBS Annual Report PDFs
# Uses pdfplumber to find the page, then Camelot to extract the table

import pdfplumber
import camelot
import re
import logging
import pandas as pd
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class UBSPDFParser:
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
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
            self.logger.info(f"Extracted year from filename: {year}")
            return year

        # Try PDF content
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages
                for page in pdf.pages[:3]:
                    text = page.extract_text()

                    # Look for "Annual Report YYYY"
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
        Find the page containing "Post-employment benefit plans" table using pdfplumber.
        Returns page number (1-indexed for Camelot).
        """

        self.logger.info("Searching for Post-employment benefit plans section...")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()

                    if not text:
                        continue

                    # Check if this page contains the benefit plans section
                    for keyword in config.PDF_TABLE_KEYWORDS:
                        if keyword.lower() in text.lower():
                            # Also check for the composition table header
                            if "composition and fair value" in text.lower():
                                # Return 1-indexed page number for Camelot
                                self.logger.info(f"Found benefit plans table on page {page_num + 1}")
                                return str(page_num + 1)

        except Exception as e:
            self.logger.error(f"Error finding benefit plans section: {e}")

        return None

    def clean_number(self, value_str):
        """Clean and convert a string to a number (handles spaces, commas, etc.)"""

        if value_str is None or value_str == '' or str(value_str).lower() == 'nan':
            return None

        # Remove spaces, commas, and other non-numeric characters except decimal point and minus
        cleaned = str(value_str).replace(' ', '').replace(',', '').replace('\xa0', '').strip()

        # Handle parentheses as negative numbers
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        # Try to convert to float
        try:
            return float(cleaned)
        except ValueError:
            return None

    def extract_table_with_camelot(self, pdf_path, page_number):
        """
        Extract the benefit plans table using Camelot.
        Returns pandas DataFrame.
        """

        self.logger.info(f"Extracting table from page {page_number} using Camelot...")

        try:
            # Use stream method (works better for tables without heavy borders)
            tables = camelot.read_pdf(
                pdf_path,
                pages=page_number,
                flavor='stream'
            )

            if len(tables) == 0:
                self.logger.error("No tables found by Camelot")
                return None

            # Get the first table (main composition table)
            table = tables[0]

            self.logger.info(f"Extracted table: {table.df.shape[0]} rows x {table.df.shape[1]} columns")
            self.logger.info(f"Table accuracy: {table.accuracy:.2f}%")

            return table.df

        except Exception as e:
            self.logger.error(f"Error extracting table with Camelot: {e}")
            return None

    def parse_camelot_table(self, df):
        """
        Parse the Camelot-extracted table and extract values.
        Returns dict with asset codes as keys and values.
        """

        self.logger.info("Parsing Camelot table...")

        data = {
            'total_assets': None,
            'percentages': {}
        }

        # Table structure (9 columns):
        # Col 0: Asset name
        # Col 1-3: 31.12.24 Fair value (Quoted, Other, Total)
        # Col 4: 31.12.24 Allocation % ⭐
        # Col 5-7: 31.12.23 Fair value
        # Col 8: 31.12.23 Allocation %

        # Skip header rows (first 5 rows: 0-4)
        data_rows = df.iloc[5:]

        # Track nested structure
        current_section = None
        current_subsection = None

        for idx, row in data_rows.iterrows():
            # Get asset name from column 0
            asset_name = str(row[0]).strip()

            if not asset_name or asset_name == '' or asset_name == 'nan':
                continue

            self.logger.debug(f"Processing row {idx}: {asset_name}")

            # Get percentage from column 4 (31.12.24 Allocation %)
            percentage_raw = str(row[4]).strip()
            percentage = self.clean_number(percentage_raw)

            # Get total fair value from column 3 (31.12.24 Total)
            total_raw = str(row[3]).strip()
            total_value = self.clean_number(total_raw)

            asset_lower = asset_name.lower()

            # Check special rows FIRST (before section/subsection logic)
            if 'total fair value of plan assets' in asset_lower:
                # Extract total (USD millions)
                self.logger.debug(f"Found 'Total fair value', total_raw='{total_raw}', total_value={total_value}")
                if total_value is not None and total_value > 10000:
                    data['total_assets'] = total_value
                    self.logger.info(f"Total assets: {total_value} USD millions")
                continue

            elif 'other investments' in asset_lower:
                self.logger.debug(f"Found 'Other investments', percentage_raw='{percentage_raw}', percentage={percentage}")
                if percentage is not None:
                    data['percentages']['OTHERINVESTMENTS'] = percentage
                    self.logger.debug(f"OTHERINVESTMENTS: {percentage}%")
                continue

            # Map asset names to codes
            if 'cash and cash equivalents' in asset_lower:
                if percentage is not None:
                    data['percentages']['CASH'] = percentage
                    self.logger.debug(f"CASH: {percentage}%")

            elif asset_lower == 'equity securities':
                current_section = 'EQUITY_SECURITIES'

            elif current_section == 'EQUITY_SECURITIES':
                if 'domestic' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICEQUITYSECURITIES'] = percentage
                        self.logger.debug(f"DOMESTICEQUITYSECURITIES: {percentage}%")
                elif 'foreign' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNEQUITYSECURITIES'] = percentage
                        self.logger.debug(f"FOREIGNEQUITYSECURITIES: {percentage}%")
                    current_section = None

            elif asset_lower == 'bonds':
                current_section = 'BONDS'

            elif current_section == 'BONDS':
                if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['NONINVESTDOMESTICBONDS'] = percentage
                        self.logger.debug(f"NONINVESTDOMESTICBONDS: {percentage}%")
                elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['NONINVESTFOREIGNBONDSRATED'] = percentage
                        self.logger.debug(f"NONINVESTFOREIGNBONDSRATED: {percentage}%")
                    current_section = None

            elif 'real estate' in asset_lower and 'property' in asset_lower:
                current_section = 'REALESTATE'

            elif current_section == 'REALESTATE':
                if 'domestic' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICREALESTATE'] = percentage
                        self.logger.debug(f"DOMESTICREALESTATE: {percentage}%")
                elif 'foreign' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNREALESTATE'] = percentage
                        self.logger.debug(f"FOREIGNREALESTATE: {percentage}%")
                    current_section = None

            elif 'investment funds' in asset_lower:
                current_section = 'INVESTMENT_FUNDS'

            # Check subsections BEFORE checking section
            elif current_subsection == 'INV_EQUITY':
                if 'domestic' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICEQUITIES'] = percentage
                        self.logger.debug(f"DOMESTICEQUITIES: {percentage}%")
                elif 'foreign' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNEQUITIES'] = percentage
                        self.logger.debug(f"FOREIGNEQUITIES: {percentage}%")
                    current_subsection = None

            elif current_subsection == 'INV_BONDS':
                if 'domestic' in asset_lower and 'aaa to bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICBONDS'] = percentage
                        self.logger.debug(f"DOMESTICBONDS: {percentage}%")
                elif 'domestic' in asset_lower and 'below bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICBONDSJUNK'] = percentage
                        self.logger.debug(f"DOMESTICBONDSJUNK: {percentage}%")
                elif 'foreign' in asset_lower and 'aaa to bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNBONDSRATED'] = percentage
                        self.logger.debug(f"FOREIGNBONDSRATED: {percentage}%")
                elif 'foreign' in asset_lower and 'below bbb' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNBONDSJUNK'] = percentage
                        self.logger.debug(f"FOREIGNBONDSJUNK: {percentage}%")
                    current_subsection = None

            elif current_subsection == 'INV_REALESTATE':
                if 'domestic' in asset_lower:
                    if percentage is not None:
                        data['percentages']['DOMESTICREALESTATEINVESTMENTS'] = percentage
                        self.logger.debug(f"DOMESTICREALESTATEINVESTMENTS: {percentage}%")
                elif 'foreign' in asset_lower:
                    if percentage is not None:
                        data['percentages']['FOREIGNREALESTATEINVESTMENTS'] = percentage
                        self.logger.debug(f"FOREIGNREALESTATEINVESTMENTS: {percentage}%")
                    current_subsection = None

            elif current_section == 'INVESTMENT_FUNDS':
                if asset_lower == 'equity':
                    current_subsection = 'INV_EQUITY'
                elif asset_lower.startswith('bonds'):
                    current_subsection = 'INV_BONDS'
                elif asset_lower == 'real estate':
                    current_subsection = 'INV_REALESTATE'
                elif asset_lower == 'other':
                    if percentage is not None:
                        data['percentages']['OTHER'] = percentage
                        self.logger.debug(f"OTHER: {percentage}%")

        return data

    def calculate_aggregated_percentages(self, percentages):
        """
        Calculate aggregated percentages for Bonds, Equities, and Real Estate.
        """

        # Calculate BONDS (sum of all bond categories)
        bonds_total = sum([
            percentages.get('NONINVESTDOMESTICBONDS', 0),
            percentages.get('NONINVESTFOREIGNBONDSRATED', 0),
            percentages.get('DOMESTICBONDS', 0),
            percentages.get('DOMESTICBONDSJUNK', 0),
            percentages.get('FOREIGNBONDSRATED', 0),
            percentages.get('FOREIGNBONDSJUNK', 0)
        ])

        # Calculate EQUITIES (sum of all equity categories)
        equities_total = sum([
            percentages.get('DOMESTICEQUITYSECURITIES', 0),
            percentages.get('FOREIGNEQUITYSECURITIES', 0),
            percentages.get('DOMESTICEQUITIES', 0),
            percentages.get('FOREIGNEQUITIES', 0)
        ])

        # Calculate REALESTATE (sum of all real estate categories)
        realestate_total = sum([
            percentages.get('DOMESTICREALESTATE', 0),
            percentages.get('FOREIGNREALESTATE', 0),
            percentages.get('DOMESTICREALESTATEINVESTMENTS', 0),
            percentages.get('FOREIGNREALESTATEINVESTMENTS', 0)
        ])

        percentages['BONDS'] = bonds_total
        percentages['EQUITIES'] = equities_total
        percentages['REALESTATE'] = realestate_total

        self.logger.info(f"Calculated aggregated percentages - Bonds: {bonds_total}%, Equities: {equities_total}%, Real Estate: {realestate_total}%")

        return percentages

    def parse_pdf(self, pdf_path):
        """
        Main method to parse a PDF report.
        Returns dict with year and all asset class data.
        """

        self.logger.info(f"\nParsing PDF: {pdf_path}")

        # Extract year
        year = self.extract_year_from_pdf(pdf_path)

        if not year:
            self.logger.error("Could not extract year from PDF")
            return None

        # Find benefit plans page using pdfplumber
        page_number = self.find_benefit_plans_page(pdf_path)

        if page_number is None:
            self.logger.error("Could not find benefit plans table")
            return None

        # Extract table using Camelot
        df = self.extract_table_with_camelot(pdf_path, page_number)

        if df is None:
            self.logger.error("Could not extract table with Camelot")
            return None

        # Parse the table
        data = self.parse_camelot_table(df)

        if not data:
            self.logger.error("Could not parse table data")
            return None

        # Calculate aggregated percentages
        data['percentages'] = self.calculate_aggregated_percentages(data['percentages'])

        # Build result dictionary
        result = {
            'year': year,
            'total_assets': data['total_assets'],
            'percentages': data['percentages']
        }

        # Validation
        if config.VALIDATE_PERCENTAGE_TOTAL:
            # Calculate total of base percentages (not including aggregated)
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
                self.logger.warning(f"Percentage total: {total_pct}% (deviation: {deviation}%)")
            else:
                self.logger.info(f"Percentage validation passed: {total_pct}%")

        self.logger.info(f"Successfully parsed {year} - Total Assets: {data['total_assets']}, Asset Classes: {len(data['percentages'])}")

        return result


def main():
    """Test the parser with a sample PDF"""
    import sys
    from logger_setup import setup_logging

    setup_logging()

    if len(sys.argv) < 2:
        print("Usage: python parser.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    parser = UBSPDFParser()
    result = parser.parse_pdf(pdf_file)

    if result:
        print(f"\nYear: {result['year']}")
        print(f"Total Assets: {result['total_assets']} USD millions")
        print(f"\nAsset Allocation Percentages:")

        for asset_code, percentage in sorted(result['percentages'].items()):
            print(f"  {asset_code}: {percentage}%")


if __name__ == '__main__':
    main()
