#!/usr/bin/env python3
# orchestrator.py
# Main orchestrator for UBS Pension Fund data collection

import os
import sys
from datetime import datetime
import config
from logger_setup import setup_logging
from scraper import UBSDownloader
from parserv2 import UBSPDFParserV2 as UBSPDFParser
from file_generator import UBSFileGenerator
import logging

logger = logging.getLogger(__name__)


def print_banner():
    """Print a welcome banner"""
    print("\n" + "="*70)
    print(" UBS Pension Fund Data Collection System")
    print(" Annual Reports - Asset Allocation & Total Assets")
    print("="*70 + "\n")


def print_configuration():
    """Print current configuration"""
    print("Configuration:")
    print("-" * 70)

    if config.TARGET_YEAR is None:
        mode = "Latest year (automatic)"
    elif isinstance(config.TARGET_YEAR, list):
        mode = f"Years: {', '.join(map(str, config.TARGET_YEAR))}"
    else:
        mode = f"Year: {config.TARGET_YEAR}"

    print(f"  Mode: {mode}")
    print(f"  Source: {config.BASE_URL}")
    print(f"  Output: {config.OUTPUT_DIR}")
    print(f"  Downloads: {config.DOWNLOAD_DIR}")
    print(f"  Timestamp: {config.RUN_TIMESTAMP}")
    print("-" * 70 + "\n")


def main():
    """Main execution flow"""

    try:
        # Setup logging
        setup_logging()

        print_banner()
        print_configuration()

        # Step 1: Download PDFs
        print("STEP 1: Downloading Annual Report PDFs")
        print("="*70)

        downloader = UBSDownloader()
        downloaded_files = downloader.download_reports()

        if not downloaded_files:
            logger.error("No files were downloaded")
            print("\n[ERROR] No files were downloaded. Exiting.")
            sys.exit(1)

        print(f"\n[SUCCESS] Downloaded {len(downloaded_files)} report(s)\n")
        logger.info(f"Downloaded {len(downloaded_files)} reports")

        # Step 2: Parse PDFs
        print("\nSTEP 2: Parsing PDF reports")
        print("="*70 + "\n")

        parser = UBSPDFParser()
        parsed_data = []

        for i, file_info in enumerate(downloaded_files, 1):
            pdf_path = file_info['file_path']
            year = file_info['year']

            print(f"[{i}/{len(downloaded_files)}] Parsing {year} report...")
            logger.info(f"Parsing report for year {year}: {pdf_path}")

            # Parse the PDF (returns list of results - one for each year in the table)
            results = parser.parse_pdf(pdf_path)

            if results:
                # The new parser extracts BOTH years from a single PDF
                for result in results:
                    parsed_data.append(result)

                    # Display extracted data
                    print(f"  Year: {result['year']}")
                    print(f"  Total Assets: {result.get('total_assets', 'N/A')} USD millions")

                    percentages = result.get('percentages', {})
                    if percentages:
                        print(f"  Asset Allocation:")
                        # Show key aggregated metrics
                        for asset in ['BONDS', 'EQUITIES', 'REALESTATE', 'CASH']:
                            if asset in percentages:
                                print(f"    {asset}: {percentages[asset]}%")

                print(f"  [SUCCESS] Extracted {len(results)} year(s) from {year} report\n")
                logger.info(f"Successfully parsed {year} report - extracted {len(results)} years")
            else:
                print(f"  [FAILED] Failed to parse PDF\n")
                logger.error(f"Failed to parse {year} report")

        if not parsed_data:
            logger.error("No data was extracted from PDFs")
            print("\n[ERROR] No data was extracted from PDFs. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Successfully parsed {len(parsed_data)} report(s)\n")
        logger.info(f"Successfully parsed {len(parsed_data)} reports")

        # Step 3: Generate output files
        print("\nSTEP 3: Generating Excel output files")
        print("="*70 + "\n")

        generator = UBSFileGenerator()
        output_files = generator.generate_files(parsed_data, config.OUTPUT_DIR)

        # Step 4: Summary
        print("\n" + "="*70)
        print(" EXECUTION COMPLETE")
        print("="*70 + "\n")

        print("Summary:")
        print(f"  Reports processed: {len(parsed_data)}")

        # Get year range
        years = sorted([d['year'] for d in parsed_data])
        if len(years) == 1:
            print(f"  Year: {years[0]}")
        else:
            print(f"  Year range: {years[0]} to {years[-1]}")

        print(f"  Time series: {len(config.OUTPUT_COLUMNS)}")
        print(f"  Asset classes: {len(set(col['asset'] for col in config.OUTPUT_COLUMNS)) - 1}")  # -1 for TOTAL
        print()

        print("Output files:")
        print(f"  DATA: {os.path.basename(output_files['data_file'])}")
        print(f"  META: {os.path.basename(output_files['meta_file'])}")
        print(f"  ZIP:  {os.path.basename(output_files['zip_file'])}")
        print()

        print(f"Output directory: {os.path.dirname(output_files['data_file'])}")
        print(f"Latest files: {config.LATEST_OUTPUT_DIR}")
        print()

        print("="*70 + "\n")

        logger.info("Orchestrator completed successfully")

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Process interrupted by user")
        logger.warning("Process interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        logger.exception("Unexpected error in orchestrator")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
