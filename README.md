# CHEF UBS Runbook

Automated data collection system for UBS Pension Fund asset allocation data from Annual Reports.

## Overview

This runbook extracts post-employment benefit plan data from UBS Annual Reports, including:
- **Total fair value of plan assets** (USD millions)
- **Asset allocation percentages** across 20 asset classes
- **Aggregated categories**: Bonds, Equities, Real Estate

## Architecture

The system follows a modular architecture with four main components:

1. **Scraper** ([scraper.py](scraper.py)) - Downloads PDF reports from UBS website
2. **Parser** ([parser.py](parser.py)) - Extracts data from PDF tables
3. **File Generator** ([file_generator.py](file_generator.py)) - Creates Excel DATA and META files
4. **Orchestrator** ([orchestrator.py](orchestrator.py)) - Coordinates the workflow

### Key Technologies

- **Selenium WebDriver**: Web scraping and PDF download
- **pdfplumber**: PDF text search and page finding
- **Camelot**: Table extraction with structure preservation (99.73% accuracy)
- **xlwt**: Excel file generation
- **pandas**: Data processing

## Data Structure

### Output Files

The system generates 3 files per run:

1. **DATA file** (`CHEF_UBS_DATA_YYYYMMDD_HHMMSS.xls`)
   - Row 0: Time series codes (21 columns)
   - Row 1: Descriptions
   - Row 2+: Annual data (Year, Total Assets, 20 allocation percentages)

2. **META file** (`CHEF_UBS_META_YYYYMMDD_HHMMSS.xls`)
   - Metadata for all 21 time series
   - 16 metadata fields per series

3. **ZIP file** (`CHEF_UBS_YYYYMMDD_HHMMSS.zip`)
   - Contains both DATA and META files

All files are also copied to `output/latest/` for easy access.

### Asset Classes (20 total)

**Individual allocations (17):**
- CASH
- DOMESTICEQUITYSECURITIES
- FOREIGNEQUITYSECURITIES
- NONINVESTDOMESTICBONDS
- NONINVESTFOREIGNBONDSRATED
- DOMESTICREALESTATE
- FOREIGNREALESTATE
- DOMESTICEQUITIES
- FOREIGNEQUITIES
- DOMESTICBONDS
- DOMESTICBONDSJUNK
- FOREIGNBONDSRATED
- FOREIGNBONDSJUNK
- DOMESTICREALESTATEINVESTMENTS
- FOREIGNREALESTATEINVESTMENTS
- OTHER
- OTHERINVESTMENTS

**Aggregated categories (3):**
- BONDS (sum of 6 bond categories)
- EQUITIES (sum of 4 equity categories)
- REALESTATE (sum of 4 real estate categories)

## Usage

### Run the complete workflow

```bash
python orchestrator.py
```

This will:
1. Download the latest UBS Annual Report PDF
2. Parse the post-employment benefit plans table
3. Generate Excel DATA, META, and ZIP files
4. Save outputs to timestamped and latest folders

### Configuration

Edit [config.py](config.py) to modify:

- `TARGET_YEAR`: Specific year(s) to download (default: `None` for latest)
- `DEBUG_MODE`: Enable detailed logging
- `DOWNLOAD_TIMEOUT`: PDF download timeout (seconds)
- `PERCENTAGE_TOLERANCE`: Validation threshold for percentage totals

### Test Individual Components

**Test scraper:**
```bash
python scraper.py
```

**Test parser:**
```bash
python parser.py <path_to_pdf>
```

**Test file generator:**
```bash
python file_generator.py
```

**Verify output structure:**
```bash
python verify_output.py
```

## Parser Implementation

The parser uses a **hybrid approach** for maximum accuracy:

1. **pdfplumber** finds the page containing keywords:
   - "Post-employment benefit plans (continued)"
   - "Composition and fair value"

2. **Camelot** extracts the table using stream method:
   - Preserves 9-column structure
   - Achieves 99.73% accuracy
   - Returns properly aligned data

3. **State machine parser** processes the table:
   - Tracks nested sections (Equity securities, Bonds, Real estate, Investment funds)
   - Handles subsections (Investment funds → Equity, Bonds, Real Estate)
   - Extracts column 4 (31.12.24 Allocation %)
   - Validates percentage totals (99% achieved)

### Critical Parser Features

- Skips 5 header rows (rows 0-4)
- Checks special rows FIRST (total assets, other investments)
- Uses `continue` statements to prevent double-processing
- Calculates aggregated percentages (BONDS, EQUITIES, REALESTATE)

## Directory Structure

```
CHEF_UBS_Runbook/
├── config.py                 # Configuration settings
├── scraper.py                # PDF downloader
├── parser.py                 # Table parser
├── file_generator.py         # Excel file generator
├── orchestrator.py           # Main workflow coordinator
├── logger_setup.py           # Logging infrastructure
├── requirements.txt          # Python dependencies
├── verify_output.py          # Output verification tool
├── README.md                 # This file
├── downloads/                # Downloaded PDFs (timestamped folders)
│   ├── YYYYMMDD_HHMMSS/
│   │   └── YYYY/
│   │       └── Annual_Report_UBS_Group_YYYY.pdf
├── output/                   # Generated files
│   ├── YYYYMMDD_HHMMSS/
│   │   ├── CHEF_UBS_DATA_YYYYMMDD_HHMMSS.xls
│   │   ├── CHEF_UBS_META_YYYYMMDD_HHMMSS.xls
│   │   └── CHEF_UBS_YYYYMMDD_HHMMSS.zip
│   └── latest/               # Latest run outputs
│       ├── CHEF_UBS_DATA_latest.xls
│       ├── CHEF_UBS_META_latest.xls
│       └── CHEF_UBS_latest.zip
└── logs/                     # Execution logs
    └── YYYYMMDD_HHMMSS/
        └── ubs_YYYYMMDD_HHMMSS.log
```

## Dependencies

```
selenium==4.15.2
pdfplumber==0.10.3
camelot-py[cv]==0.11.0
pandas==2.1.3
xlwt==1.3.0
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Testing Results

**Last successful run (2024-12-03):**
- Year: 2024
- Total Assets: 52,241 USD millions
- Asset Classes: 20/20 extracted (100%)
- Percentage Validation: 99% (passed)
- Camelot Accuracy: 99.73%
- Files Generated: DATA, META, ZIP ✓

## Source

**URL:** https://www.ubs.com/global/en/investor-relations/financial-information/annual-reporting.html

**Target Table:** Post-employment benefit plans - Composition and fair value of Swiss defined benefit plan assets

**Data Location:** Page 361 in 2024 Annual Report (may vary by year)

## Notes

- The parser automatically handles cookie consent on the UBS website
- PDFs are downloaded to timestamped folders to avoid overwriting
- The system validates percentage totals within 2% tolerance
- All runs are logged to timestamped log files for debugging
- Column 4 in the Camelot-extracted table contains the current year allocation percentages

## Maintenance

If the table structure changes in future reports:
1. Update `PDF_TABLE_KEYWORDS` in [config.py](config.py)
2. Adjust row skipping logic in `parse_camelot_table()` if needed
3. Test with `python parser.py <path_to_new_pdf>` to verify extraction
4. Check percentage validation to ensure all categories are captured

## Author

Created following the CHEF_NOVARTIS runbook architecture pattern.
