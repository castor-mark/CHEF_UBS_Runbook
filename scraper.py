# scraper.py
# Downloads Annual Report PDFs from UBS website

import os
import time
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config
import requests

# Setup logging
logger = logging.getLogger(__name__)


class UBSDownloader:
    """Downloads annual report PDFs from UBS website"""

    def __init__(self):
        self.driver = None
        self.download_dir = None
        self.logger = logger

    def setup_driver(self):
        """Initialize Chrome driver with download preferences"""

        # Create download directory with timestamp
        self.download_dir = os.path.abspath(config.DOWNLOAD_DIR)
        os.makedirs(self.download_dir, exist_ok=True)

        chrome_options = Options()

        # Set download directory
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # Don't open in browser
            "plugins.plugins_disabled": ["Chrome PDF Viewer"]
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if config.HEADLESS_MODE:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(config.WAIT_TIMEOUT)

        self.logger.info(f"Chrome driver initialized")
        self.logger.info(f"Download directory: {self.download_dir}")

    def navigate_to_page(self):
        """Navigate to the UBS annual reporting page"""

        self.logger.info(f"Navigating to {config.BASE_URL}")

        self.driver.get(config.BASE_URL)
        time.sleep(config.PAGE_LOAD_DELAY)

        self.logger.info("Page loaded successfully")

    def handle_cookie_consent(self):
        """Click 'Agree to all' on cookie consent banner"""

        self.logger.info("Handling cookie consent...")

        try:
            # Wait for cookie consent button to appear
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            consent_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, config.SELECTORS['cookie_agree_all']))
            )

            self.logger.info("Cookie consent dialog found")
            consent_button.click()
            time.sleep(2)  # Wait for dialog to close

            self.logger.info("Cookie consent accepted")
            return True

        except TimeoutException:
            self.logger.warning("Cookie consent dialog not found (may have been accepted previously)")
            return False
        except Exception as e:
            self.logger.error(f"Error handling cookie consent: {e}")
            return False

    def scroll_to_reporting_suite(self):
        """Scroll down to the Reporting Suite section"""

        self.logger.info("Scrolling to Reporting Suite section...")

        try:
            # Find all section headers
            section_headers = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['reporting_suite_section'])

            for section in section_headers:
                try:
                    title_element = section.find_element(By.CSS_SELECTOR, config.SELECTORS['section_title'])
                    title = title_element.text.strip()

                    if 'Reporting Suite' in title:
                        # Scroll to this section
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            section
                        )
                        time.sleep(2)
                        self.logger.info("Scrolled to Reporting Suite section")
                        return True

                except NoSuchElementException:
                    continue

            self.logger.error("Reporting Suite section not found")
            return False

        except Exception as e:
            self.logger.error(f"Error scrolling to Reporting Suite: {e}")
            return False

    def extract_year_from_text(self, text):
        """Extract year from report title (e.g., 'Annual Report 2024' -> 2024)"""

        # Look for 4-digit year
        match = re.search(r'(\d{4})', text)
        if match:
            return match.group(1)
        return None

    def get_ubs_group_report_link(self):
        """
        Find and extract the 'Annual Report XXXX – UBS Group' link.
        Returns dict with year, title, and digital_report_url.
        """

        self.logger.info("Looking for UBS Group Annual Report link...")

        try:
            # Find all report containers
            report_containers = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['report_container'])

            for container in report_containers:
                try:
                    # Look for Annual Report title
                    h3_elements = container.find_elements(By.TAG_NAME, 'h3')

                    for h3 in h3_elements:
                        title_text = h3.text.strip()

                        # Look for "Annual Report" in title
                        if 'Annual Report' in title_text:
                            self.logger.info(f"Found section: {title_text}")

                            # Extract year from title
                            year = self.extract_year_from_text(title_text)

                            if not year:
                                continue

                            # Find the link list within this container
                            link_items = container.find_elements(By.CSS_SELECTOR, config.SELECTORS['report_links'])

                            for item in link_items:
                                try:
                                    anchor = item.find_element(By.CSS_SELECTOR, config.SELECTORS['report_link_anchor'])
                                    link_text = anchor.text.strip()
                                    link_url = anchor.get_attribute('href')

                                    # Look for "Annual Report XXXX – UBS Group" (digital version)
                                    if f'Annual Report {year}' in link_text and 'UBS Group' in link_text and 'digital' in link_url.lower():
                                        self.logger.info(f"Found UBS Group report: {link_text}")

                                        return {
                                            'year': year,
                                            'title': link_text,
                                            'digital_report_url': link_url
                                        }

                                except Exception as e:
                                    self.logger.debug(f"Error processing link: {e}")
                                    continue

                except Exception as e:
                    self.logger.debug(f"Error processing container: {e}")
                    continue

            self.logger.error("UBS Group Annual Report link not found")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting report link: {e}")
            return None

    def navigate_to_digital_report(self, digital_report_url):
        """Navigate to the digital report page"""

        self.logger.info(f"Navigating to digital report: {digital_report_url}")

        try:
            self.driver.get(digital_report_url)
            time.sleep(config.PAGE_LOAD_DELAY)
            self.logger.info("Digital report page loaded")
            return True

        except Exception as e:
            self.logger.error(f"Error navigating to digital report: {e}")
            return False

    def find_download_button(self):
        """
        Find the download button (tries navbar first, then body).
        Returns the download URL if found.
        """

        self.logger.info("Looking for PDF download button...")

        try:
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)

            # Try navbar download button first
            try:
                navbar_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS['navbar_download_button']))
                )

                pdf_url = navbar_button.get_attribute('href')
                if pdf_url:
                    self.logger.info(f"Found navbar download button: {pdf_url}")
                    return pdf_url

            except TimeoutException:
                self.logger.info("Navbar download button not found, trying body button...")

            # Try body download button
            try:
                body_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS['body_download_button']))
                )

                pdf_url = body_button.get_attribute('href')
                if pdf_url:
                    self.logger.info(f"Found body download button: {pdf_url}")
                    return pdf_url

            except TimeoutException:
                self.logger.error("Body download button not found either")

            return None

        except Exception as e:
            self.logger.error(f"Error finding download button: {e}")
            return None

    def download_pdf_direct(self, pdf_url, year, title):
        """
        Download PDF directly using requests.
        Returns the local file path if successful.
        """

        self.logger.info(f"Downloading PDF for {year}...")

        try:
            # Create year subdirectory
            year_dir = os.path.join(self.download_dir, year)
            os.makedirs(year_dir, exist_ok=True)

            # Generate filename
            filename = f"Annual_Report_UBS_Group_{year}.pdf"
            expected_file = os.path.join(year_dir, filename)

            # Check if file already exists
            if os.path.exists(expected_file) and os.path.getsize(expected_file) > 100000:
                self.logger.info(f"Cached: {year} - {filename}")
                return expected_file

            # Download with requests
            self.logger.info(f"Downloading from: {pdf_url}")
            response = requests.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            # Save file
            with open(expected_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file size
            file_size = os.path.getsize(expected_file)
            if file_size > 100000:
                self.logger.info(f"Downloaded: {year} - {file_size} bytes")
                return expected_file
            else:
                os.remove(expected_file)
                self.logger.error(f"Download failed - file too small: {year}")
                return None

        except Exception as e:
            self.logger.error(f"Download failed for {year}: {e}")
            return None

    def download_reports(self):
        """
        Main method to download reports based on configuration.
        Returns list of downloaded file paths and metadata.
        """

        try:
            self.setup_driver()
            self.navigate_to_page()

            # Handle cookie consent
            self.handle_cookie_consent()

            # Scroll to Reporting Suite
            if not self.scroll_to_reporting_suite():
                self.logger.error("Failed to scroll to Reporting Suite")
                return []

            # Get UBS Group report link
            report_info = self.get_ubs_group_report_link()

            if not report_info:
                self.logger.error("Failed to find UBS Group report link")
                return []

            print(f"\n{'='*60}")
            print(f"Found Report: {report_info['title']}")
            print(f"Year: {report_info['year']}")
            print(f"{'='*60}\n")

            # Navigate to digital report page
            if not self.navigate_to_digital_report(report_info['digital_report_url']):
                self.logger.error("Failed to navigate to digital report")
                return []

            # Find download button
            pdf_url = self.find_download_button()

            if not pdf_url:
                self.logger.error("Failed to find download button")
                return []

            # Download the PDF
            file_path = self.download_pdf_direct(
                pdf_url,
                report_info['year'],
                report_info['title']
            )

            if file_path:
                print(f"\n{'='*60}")
                print(f"Download complete: {report_info['year']}")
                print(f"{'='*60}\n")

                return [{
                    'year': report_info['year'],
                    'title': report_info['title'],
                    'file_path': file_path
                }]
            else:
                return []

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    """Test the downloader"""
    from logger_setup import setup_logging

    setup_logging()

    downloader = UBSDownloader()
    results = downloader.download_reports()

    print("\nDownloaded files:")
    for result in results:
        print(f"  {result['year']}: {result['file_path']}")


if __name__ == '__main__':
    main()
