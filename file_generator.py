# file_generator.py
# Generate Excel DATA and META files for UBS Pension Fund dataset

import os
import xlwt
import zipfile
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class UBSFileGenerator:
    """Generates Excel DATA and META files in the required format"""

    def __init__(self):
        self.debug = config.DEBUG_MODE
        self.logger = logger

    def create_data_file(self, data_records, output_path):
        """
        Create the DATA Excel file with the exact column structure from config.

        Args:
            data_records: List of dicts with 'year', 'total_assets', and 'percentages'
            output_path: Path to save the Excel file

        Returns:
            Path to created file
        """

        self.logger.info(f"Creating DATA file with {len(data_records)} records")

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('DATA')

        # Create number format styles
        # Format for large numbers (USD millions): #,##0 (no decimals)
        number_style_millions = xlwt.XFStyle()
        number_style_millions.num_format_str = '#,##0'

        # Format for percentages: #,##0 (no decimals)
        number_style_percent = xlwt.XFStyle()
        number_style_percent.num_format_str = '#,##0'

        # Row 0: Codes
        for col_idx, col_info in enumerate(config.OUTPUT_COLUMNS):
            sheet.write(0, col_idx + 1, col_info['code'])  # +1 because col 0 is empty

        # Row 1: Descriptions
        for col_idx, col_info in enumerate(config.OUTPUT_COLUMNS):
            sheet.write(1, col_idx + 1, col_info['description'])

        # Sort data records by year
        data_records.sort(key=lambda x: x['year'])

        # Data rows (starting from row 2)
        for row_idx, record in enumerate(data_records, start=2):
            year = record['year']
            total_assets = record['total_assets']
            percentages = record['percentages']

            # Write year in first column (format: YYYY)
            sheet.write(row_idx, 0, year)

            # Write values for each column
            for col_idx, col_info in enumerate(config.OUTPUT_COLUMNS):
                asset_code = col_info['asset']
                metric_code = col_info['metric']

                value = None
                style = None

                if metric_code == 'LEVEL' and asset_code == 'TOTAL':
                    # Total assets value
                    value = total_assets
                    style = number_style_millions

                elif metric_code == 'ACTUALALLOCATION':
                    # Percentage allocation
                    value = percentages.get(asset_code)
                    style = number_style_percent

                # Write value if it exists with proper formatting
                if value is not None:
                    sheet.write(row_idx, col_idx + 1, value, style)

        # Save the file
        workbook.save(output_path)
        self.logger.info(f"DATA file saved: {output_path}")

        return output_path

    def create_meta_file(self, output_path):
        """
        Create the META Excel file with metadata for all time series.

        Args:
            output_path: Path to save the Excel file

        Returns:
            Path to created file
        """

        self.logger.info("Creating META file")

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('META')

        # Header row
        for col_idx, col_name in enumerate(config.METADATA_COLUMNS):
            sheet.write(0, col_idx, col_name)

        # Data rows - one for each time series
        for row_idx, col_info in enumerate(config.OUTPUT_COLUMNS, start=1):
            code = col_info['code']
            description = col_info['description']
            multiplier = col_info['multiplier']

            # Write metadata for this time series
            row_data = {
                'CODE': code,
                'DESCRIPTION': description,
                'FREQUENCY': config.METADATA_DEFAULTS['FREQUENCY'],
                'MULTIPLIER': multiplier,
                'AGGREGATION_TYPE': config.METADATA_DEFAULTS['AGGREGATION_TYPE'],
                'UNIT_TYPE': config.METADATA_DEFAULTS['UNIT_TYPE'],
                'DATA_TYPE': config.METADATA_DEFAULTS['DATA_TYPE'],
                'DATA_UNIT': config.METADATA_DEFAULTS['DATA_UNIT'],
                'SEASONALLY_ADJUSTED': config.METADATA_DEFAULTS['SEASONALLY_ADJUSTED'],
                'ANNUALIZED': config.METADATA_DEFAULTS['ANNUALIZED'],
                'PROVIDER_MEASURE_URL': config.METADATA_DEFAULTS['PROVIDER_MEASURE_URL'],
                'PROVIDER': config.METADATA_DEFAULTS['PROVIDER'],
                'SOURCE': config.METADATA_DEFAULTS['SOURCE'],
                'SOURCE_DESCRIPTION': config.METADATA_DEFAULTS['SOURCE_DESCRIPTION'],
                'COUNTRY': config.METADATA_DEFAULTS['COUNTRY'],
                'DATASET': config.METADATA_DEFAULTS['DATASET']
            }

            # Write each column
            for col_idx, col_name in enumerate(config.METADATA_COLUMNS):
                value = row_data.get(col_name, '')
                sheet.write(row_idx, col_idx, value)

        # Save the file
        workbook.save(output_path)
        self.logger.info(f"META file saved: {output_path}")

        return output_path

    def create_zip_file(self, data_file, meta_file, zip_path):
        """
        Create a ZIP file containing the DATA and META files.

        Args:
            data_file: Path to DATA file
            meta_file: Path to META file
            zip_path: Path for output ZIP file

        Returns:
            Path to created ZIP file
        """

        self.logger.info(f"Creating ZIP file: {zip_path}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files with just their basename (no path)
            zipf.write(data_file, os.path.basename(data_file))
            zipf.write(meta_file, os.path.basename(meta_file))

        self.logger.info(f"ZIP file created: {zip_path}")

        return zip_path

    def generate_files(self, parsed_data, output_dir):
        """
        Generate DATA, META, and ZIP files from parsed data.

        Args:
            parsed_data: List of dicts with 'year', 'total_assets', 'percentages'
            output_dir: Directory to save output files

        Returns:
            Dict with paths to created files
        """

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filenames with timestamp
        timestamp = config.RUN_TIMESTAMP
        data_filename = config.DATA_FILE_PATTERN.format(timestamp=timestamp)
        meta_filename = config.META_FILE_PATTERN.format(timestamp=timestamp)
        zip_filename = config.ZIP_FILE_PATTERN.format(timestamp=timestamp)

        data_path = os.path.join(output_dir, data_filename)
        meta_path = os.path.join(output_dir, meta_filename)
        zip_path = os.path.join(output_dir, zip_filename)

        # Create files
        self.create_data_file(parsed_data, data_path)
        self.create_meta_file(meta_path)
        zip_file = self.create_zip_file(data_path, meta_path, zip_path)

        # Also copy to 'latest' folder
        latest_dir = config.LATEST_OUTPUT_DIR
        os.makedirs(latest_dir, exist_ok=True)

        latest_data_path = os.path.join(latest_dir, f"CHEF_UBS_DATA_latest.xls")
        latest_meta_path = os.path.join(latest_dir, f"CHEF_UBS_META_latest.xls")
        latest_zip_path = os.path.join(latest_dir, f"CHEF_UBS_latest.zip")

        # Copy to latest folder
        import shutil
        shutil.copy2(data_path, latest_data_path)
        shutil.copy2(meta_path, latest_meta_path)
        shutil.copy2(zip_path, latest_zip_path)

        self.logger.info("Files also copied to 'latest' folder")

        return {
            'data_file': data_path,
            'meta_file': meta_path,
            'zip_file': zip_file,
            'latest_data': latest_data_path,
            'latest_meta': latest_meta_path,
            'latest_zip': latest_zip_path
        }


def main():
    """Test the file generator with sample data"""
    import sys
    from logger_setup import setup_logging

    setup_logging()

    # Sample data for testing (using 2024 actual parsed data)
    sample_data = [
        {
            'year': '2024',
            'total_assets': 52241.0,
            'percentages': {
                'CASH': 2.0,
                'DOMESTICEQUITYSECURITIES': 0.0,
                'FOREIGNEQUITYSECURITIES': 3.0,
                'NONINVESTDOMESTICBONDS': 0.0,
                'NONINVESTFOREIGNBONDSRATED': 0.0,
                'DOMESTICREALESTATE': 11.0,
                'FOREIGNREALESTATE': 2.0,
                'DOMESTICEQUITIES': 2.0,
                'FOREIGNEQUITIES': 20.0,
                'DOMESTICBONDS': 13.0,
                'DOMESTICBONDSJUNK': 0.0,
                'FOREIGNBONDSRATED': 25.0,
                'FOREIGNBONDSJUNK': 3.0,
                'DOMESTICREALESTATEINVESTMENTS': 4.0,
                'FOREIGNREALESTATEINVESTMENTS': 1.0,
                'OTHER': 9.0,
                'OTHERINVESTMENTS': 4.0,
                'BONDS': 41.0,
                'EQUITIES': 25.0,
                'REALESTATE': 18.0
            }
        },
        {
            'year': '2023',
            'total_assets': 54404.0,
            'percentages': {
                'CASH': 2.0,
                'DOMESTICEQUITYSECURITIES': 0.0,
                'FOREIGNEQUITYSECURITIES': 4.0,
                'NONINVESTDOMESTICBONDS': 0.0,
                'NONINVESTFOREIGNBONDSRATED': 0.0,
                'DOMESTICREALESTATE': 11.0,
                'FOREIGNREALESTATE': 2.0,
                'DOMESTICEQUITIES': 3.0,
                'FOREIGNEQUITIES': 19.0,
                'DOMESTICBONDS': 15.0,
                'DOMESTICBONDSJUNK': 0.0,
                'FOREIGNBONDSRATED': 25.0,
                'FOREIGNBONDSJUNK': 2.0,
                'DOMESTICREALESTATEINVESTMENTS': 4.0,
                'FOREIGNREALESTATEINVESTMENTS': 1.0,
                'OTHER': 10.0,
                'OTHERINVESTMENTS': 2.0,
                'BONDS': 42.0,
                'EQUITIES': 26.0,
                'REALESTATE': 18.0
            }
        }
    ]

    generator = UBSFileGenerator()
    result = generator.generate_files(sample_data, config.OUTPUT_DIR)

    print("\nGenerated files:")
    for key, path in result.items():
        print(f"  {key}: {path}")


if __name__ == '__main__':
    main()
