# config.py
# UBS Post-Employment Benefit Plans Data Collection Configuration

import os
from datetime import datetime

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

BASE_URL = 'https://www.ubs.com/global/en/investor-relations/financial-information/annual-reporting.html'
PROVIDER_NAME = 'UBS Group'
DATASET_NAME = 'UBS'
COUNTRY = 'Switzerland'
CURRENCY = 'USD'

# =============================================================================
# TIMESTAMPED FOLDERS CONFIGURATION
# =============================================================================

# Generate timestamp for this run (format: YYYYMMDD_HHMMSS)
RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Use timestamped folders to avoid conflicts between runs
USE_TIMESTAMPED_FOLDERS = True

# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

# Target year for data extraction
# Set to None to auto-detect most recent year (latest available)
# Format: 2024, 2023, etc.
TARGET_YEAR = None   # Options: None (latest), 2024, 2023, 2022, etc.

# When set to True, process all available years
PROCESS_ALL_YEARS = False

# =============================================================================
# WEB SCRAPING SELECTORS (from site inspection)
# =============================================================================

SELECTORS = {
    # Cookie consent
    'cookie_banner': 'div.privacysettings__banner',
    'cookie_agree_all': 'button[data-ps-tracking-button-version="acceptAll"]',

    # Reporting Suite section
    'reporting_suite_section': 'div.sectionheader__base',
    'section_title': 'h2.sectionheader__hl',

    # Annual Report container
    'report_container': 'div.gridcontrol3__row',
    'report_title': 'h3',
    'report_links': 'ul.linklistnewlook__list li.linklistnewlook__listItem',
    'report_link_anchor': 'a',

    # Download button selectors (navbar)
    'navbar_download_button': 'div.header-pdf-download-button a.download-button',

    # Download button selectors (body - alternative)
    'body_download_button': 'div.body-pdf-download-button a.download-button',
    'main_content': 'main.content',
}

# =============================================================================
# PDF PARSING CONFIGURATION
# =============================================================================

# Keywords to find "Post-employment benefit plans" section
PDF_TABLE_KEYWORDS = [
    "Post-employment benefit plans (continued)",
    "Post-employment benefit plans",
    "Composition and fair value of Swiss defined benefit plan assets",
    "Note 26 Post-employment benefit plans"
]

# Table column headers to look for
PDF_TABLE_HEADERS = [
    "31.12.",  # Date pattern for columns (31.12.24, 31.12.23)
    "Fair value",
    "Plan asset allocation %",
    "USD m"
]

# Asset class names in PDF (map to output codes)
# Based on the sample data structure
PDF_ASSET_NAMES = {
    'CASH': ['Cash and cash equivalents'],
    'DOMESTICEQUITYSECURITIES': ['Equity securities', 'Domestic'],
    'FOREIGNEQUITYSECURITIES': ['Equity securities', 'Foreign'],
    'NONINVESTDOMESTICBONDS': ['Bonds', 'Domestic, AAA to BBB–'],
    'NONINVESTFOREIGNBONDSRATED': ['Bonds', 'Foreign, AAA to BBB–'],
    'DOMESTICREALESTATE': ['Real estate / property', 'Domestic'],
    'FOREIGNREALESTATE': ['Real estate / property', 'Foreign'],
    'DOMESTICEQUITIES': ['Investment funds', 'Equity', 'Domestic'],
    'FOREIGNEQUITIES': ['Investment funds', 'Equity', 'Foreign'],
    'DOMESTICBONDS': ['Investment funds', 'Bonds', 'Domestic, AAA to BBB–'],
    'DOMESTICBONDSJUNK': ['Investment funds', 'Bonds', 'Domestic, below BBB–'],
    'FOREIGNBONDSRATED': ['Investment funds', 'Bonds', 'Foreign, AAA to BBB–'],
    'FOREIGNBONDSJUNK': ['Investment funds', 'Bonds', 'Foreign, below BBB–'],
    'DOMESTICREALESTATEINVESTMENTS': ['Investment funds', 'Real estate', 'Domestic'],
    'FOREIGNREALESTATEINVESTMENTS': ['Investment funds', 'Real estate', 'Foreign'],
    'OTHER': ['Investment funds', 'Other'],
    'OTHERINVESTMENTS': ['Other investments'],
    'TOTAL': ['Total fair value of plan assets']
}

# =============================================================================
# OUTPUT COLUMN STRUCTURE (EXACT ORDER - DO NOT CHANGE)
# =============================================================================

# Based on CHEF_UBS_DATA_20250319 - DATA.csv
# Column order is ABSOLUTE and must match exactly

OUTPUT_COLUMNS = [
    {
        'code': 'UBS.TOTAL.LEVEL.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Total fair value of plan asset',
        'asset': 'TOTAL',
        'metric': 'LEVEL',
        'unit': 'USD millions',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.CASH.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Cash and cash equivalents',
        'asset': 'CASH',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICEQUITYSECURITIES.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Equity securities, Domestic',
        'asset': 'DOMESTICEQUITYSECURITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNEQUITYSECURITIES.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Equity securities, Foreign',
        'asset': 'FOREIGNEQUITYSECURITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.NONINVESTDOMESTICBONDS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Non investment fund Domestic, AAA to BBB–',
        'asset': 'NONINVESTDOMESTICBONDS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.NONINVESTFOREIGNBONDSRATED.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Non investment fund Foreign, AAA to BBB–',
        'asset': 'NONINVESTFOREIGNBONDSRATED',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICREALESTATE.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Real estate / property, Domestic',
        'asset': 'DOMESTICREALESTATE',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNREALESTATE.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Real estate / property, Foreign',
        'asset': 'FOREIGNREALESTATE',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICEQUITIES.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Equity, Domestic',
        'asset': 'DOMESTICEQUITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNEQUITIES.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Equity, Foreign',
        'asset': 'FOREIGNEQUITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICBONDS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Bonds, Domestic, AAA to BBB–',
        'asset': 'DOMESTICBONDS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICBONDSJUNK.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Bonds, Domestic, below BBB–',
        'asset': 'DOMESTICBONDSJUNK',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNBONDSRATED.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Bonds, Foreign, AAA to BBB–',
        'asset': 'FOREIGNBONDSRATED',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNBONDSJUNK.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Bonds, Foreign, below BBB–',
        'asset': 'FOREIGNBONDSJUNK',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.DOMESTICREALESTATEINVESTMENTS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Domestic Real estate Investments',
        'asset': 'DOMESTICREALESTATEINVESTMENTS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.FOREIGNREALESTATEINVESTMENTS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Foreign Real estate Investments',
        'asset': 'FOREIGNREALESTATEINVESTMENTS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.OTHER.ACTUALALLOCATION.INDIRECT.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Other',
        'asset': 'OTHER',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.OTHERINVESTMENTS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Other Investments',
        'asset': 'OTHERINVESTMENTS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'table',
        'multiplier': 0.0
    },
    {
        'code': 'UBS.BONDS.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Bonds',
        'asset': 'BONDS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'calculated',  # Sum of bond categories
        'multiplier': 0.0
    },
    {
        'code': 'UBS.EQUITIES.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Equity',
        'asset': 'EQUITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'calculated',  # Sum of equity categories
        'multiplier': 0.0
    },
    {
        'code': 'UBS.REALESTATE.ACTUALALLOCATION.NONE.A.1@UBS',
        'description': 'Post-employment benefit plans, Actual Allocation, Real estate / property',
        'asset': 'REALESTATE',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'calculated',  # Sum of real estate categories
        'multiplier': 0.0
    }
]

# =============================================================================
# METADATA STANDARD FIELDS
# =============================================================================

METADATA_DEFAULTS = {
    'FREQUENCY': 'A',  # Annual
    'AGGREGATION_TYPE': 'END_OF_PERIOD',
    'UNIT_TYPE': 'LEVEL',
    'DATA_TYPE': 'CURRENCY',
    'DATA_UNIT': CURRENCY,
    'SEASONALLY_ADJUSTED': 'NSA',
    'ANNUALIZED': False,
    'PROVIDER_MEASURE_URL': BASE_URL,
    'PROVIDER': 'AfricaAI',
    'SOURCE': 'UBS',
    'SOURCE_DESCRIPTION': PROVIDER_NAME,
    'COUNTRY': COUNTRY,
    'DATASET': DATASET_NAME
}

# Metadata file columns
METADATA_COLUMNS = [
    'CODE',
    'DESCRIPTION',
    'FREQUENCY',
    'MULTIPLIER',
    'AGGREGATION_TYPE',
    'UNIT_TYPE',
    'DATA_TYPE',
    'DATA_UNIT',
    'SEASONALLY_ADJUSTED',
    'ANNUALIZED',
    'PROVIDER_MEASURE_URL',
    'PROVIDER',
    'SOURCE',
    'SOURCE_DESCRIPTION',
    'COUNTRY',
    'DATASET'
]

# =============================================================================
# DATE FORMATS
# =============================================================================

DATE_FORMAT_OUTPUT = '%Y'  # Annual format (YYYY)
DATETIME_FORMAT_META = '%Y-%m-%d %H:%M:%S'
FILENAME_DATE_FORMAT = '%Y%m%d'

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

HEADLESS_MODE = False
DEBUG_MODE = True
WAIT_TIMEOUT = 20
PAGE_LOAD_DELAY = 3
DOWNLOAD_WAIT_TIME = 15  # Wait time for PDF download

# =============================================================================
# DOWNLOAD CONFIGURATION
# =============================================================================

# Parallel downloads (faster for multiple years)
PARALLEL_DOWNLOADS = False  # UBS may have rate limiting
MAX_WORKERS = 2
DOWNLOAD_DELAY = 2.0  # Seconds between requests

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Base directories
BASE_DOWNLOAD_DIR = './downloads'
BASE_OUTPUT_DIR = './output'
BASE_LOG_DIR = './logs'

# Apply timestamping if enabled
if USE_TIMESTAMPED_FOLDERS:
    DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, RUN_TIMESTAMP)
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, RUN_TIMESTAMP)
    LOG_DIR = os.path.join(BASE_LOG_DIR, RUN_TIMESTAMP)
else:
    DOWNLOAD_DIR = BASE_DOWNLOAD_DIR
    OUTPUT_DIR = BASE_OUTPUT_DIR
    LOG_DIR = BASE_LOG_DIR

# Latest folder (always contains most recent extraction)
LATEST_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'latest')

# File naming patterns
DATA_FILE_PATTERN = 'CHEF_UBS_DATA_{timestamp}.xls'
META_FILE_PATTERN = 'CHEF_UBS_META_{timestamp}.xls'
ZIP_FILE_PATTERN = 'CHEF_UBS_{timestamp}.zip'

# Log file naming
LOG_FILE_PATTERN = 'ubs_{timestamp}.log'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Console output
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# =============================================================================
# PDF PARSING LIBRARIES
# =============================================================================

# Use pdfplumber for table extraction
USE_PDFPLUMBER = True
USE_CAMELOT = True  # Backup option

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

# Validate that all required asset classes are found
REQUIRE_ALL_ASSETS = True

# Validate percentage totals (should sum to 100% or close)
VALIDATE_PERCENTAGE_TOTAL = True
PERCENTAGE_TOLERANCE = 2.0  # Allow 2% deviation from 100%

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Continue processing even if some PDFs fail
CONTINUE_ON_ERROR = True

# Maximum retries for download failures
MAX_DOWNLOAD_RETRIES = 3
RETRY_DELAY = 2.0  # Seconds between retries
