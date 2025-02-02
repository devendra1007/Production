import os
import time
import re
from datetime import datetime, timedelta
import pandas as pd
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from playwright.sync_api import sync_playwright
import logging
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
import pytz


# Set up directories
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(base_dir, 'logs')
config_dir = os.path.join(base_dir, 'config')
download_dir = os.path.join(base_dir, 'downloads')
load_dotenv(os.path.join(base_dir, '.env'))

# Create necessary directories
os.makedirs(log_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)
os.makedirs(download_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'task.log'), mode='a'),
        logging.StreamHandler()
    ]
)

# ===========================
# Decorators
# ===========================

def retry_with_delay(attempts=5, delay=60):
    """Decorator to retry a function with a delay between attempts."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < attempts - 1:
                        logging.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
            raise Exception(f"All {attempts} attempts failed.")
        return wrapper
    return decorator

# ===========================
# Google Sheets Operations
# ===========================

def write_sheet_data(spreadsheet_id, range_name, values, credentials):
    """Write data to a Google Sheets document."""
    service = build('sheets', 'v4', credentials=credentials)
    
    # Clear the existing data in the specified range
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    # Prepare the new data to be written
    body = {'values': values}
    
    # Write the new data to the specified range
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

def get_user_credentials():
    """Get user credentials for Google Sheets API."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    token_path = os.path.join(config_dir, 'token.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(config_dir, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds

# ===========================
# Browser Operations
# ===========================

def launch_browser(headless=True):
    """Launch a fresh Chrome browser instance without persistent data using new headless mode."""
    playwright = sync_playwright().start()
    args = [
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--start-maximized',
        '--incognito',
    ]
    if headless:
        args.append('--headless=new')
    
    browser = playwright.chromium.launch(
        channel="chrome",
        headless=False,  # Disable built-in headless to use the new flag instead.
        args=args,
        timeout=120000  # Increase browser launch timeout to 120 seconds
    )
    
    context = browser.new_context(
        viewport={'width': 1440, 'height': 810},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        accept_downloads=True
    )
    
    page = context.new_page()
    
    return browser, playwright, page

def wait_for_page_load(page, timeout=60000):
    """Wait for page to be fully loaded."""
    try:
        page.wait_for_load_state('domcontentloaded', timeout=timeout)
        page.wait_for_load_state('networkidle', timeout=timeout)
        page.wait_for_load_state('load', timeout=timeout)
        logging.info("Page loaded successfully.")
    except Exception as e:
        logging.warning(f"Wait for page load warning: {str(e)}")

def wait_for_element(page, selector, timeout=60000):
    """Wait for an element to be visible and stable."""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        page.wait_for_timeout(1000)  # Small delay to ensure stability
        logging.info(f"Element '{selector}' is visible.")
        return element
    except Exception as e:
        logging.warning(f"Wait for element failed: {str(e)}")
        return None

@retry_with_delay(attempts=5, delay=30)
def click_element(page, role, name, exact=True):
    """Click an element based on its role and name."""
    page.get_by_role(role, name=name, exact=exact).click()


# ===========================
# Data Transformation
# ===========================

def transform_dataframe(df):
    """Transform the DataFrame to extract transaction totals and summaries."""
    transaction_totals_str = df.iloc[0, 0]
    transaction_totals = {}
    
    try:
        matches = re.findall(r'(\w+): (\d+)', transaction_totals_str)
        transaction_totals = {key: value for key, value in matches}
    except Exception as e:
        print(f"Error parsing transaction totals: {e}")
        return None
    
    new_data = {
        'Transaction Totals:': [f"Visa: {transaction_totals.get('Visa', '0')}", 
                                f"MasterCard: {transaction_totals.get('MasterCard', '0')}", 
                                f"American Express: {transaction_totals.get('American', '0')}", 
                                f"Discover: {transaction_totals.get('Discover', '0')}", 
                                f"Apple Pay: {transaction_totals.get('Apple', '0')}", 
                                f"ACH (eCheck): {transaction_totals.get('ACH', '0')}"],
        'Sales Summary': df.iloc[3:9, 0].fillna('').values,
        'Declined Summary': df.iloc[3:9, 4].fillna('').values,
        'Credit Summary': df.iloc[3:9, 8].fillna('').values,
        'Net Total': df.iloc[3:9, 12].fillna('').values
    }
    
    new_df = pd.DataFrame(new_data)
    
    total_row = pd.DataFrame({
        'Transaction Totals:': [f"Total sales: {df.iloc[9, 0].split(': ')[1]}"],
        'Sales Summary': [f"Total sales: {df.iloc[9, 0].split(': ')[1]}"],
        'Declined Summary': [f"Total declined: {df.iloc[9, 4].split(': ')[1]}"],
        'Credit Summary': [f"Total credit: {df.iloc[9, 8].split(': ')[1]}"],
        'Net Total': [f"Total net: {df.iloc[9, 12].split(': ')[1]}"]
    })
    
    new_df = pd.concat([new_df, total_row], ignore_index=True)
    
    return new_df

# ===========================
# Report Downloading
# ===========================

def change_report_format_and_download(page, download_dir, file_name):
    """Change report format and download the report."""
    logging.info("Attempting to change report format and download")

    page.get_by_label("Change report format").click()
    page.get_by_role("cell", name="View in Excel Options View in").click()

    with page.expect_download(timeout=90000) as download_info:
        page.get_by_role("cell", name="View in CSV Format View in").click()

    download = download_info.value
    save_path = os.path.join(download_dir, f"{file_name}.csv")
    download.save_as(save_path)

    logging.info("Report downloaded successfully")

def download_comtec_report(page, download_dir, file_name='comtec_export.csv'):
    """
    Download the Comtec report.
    Args:
        page: Playwright page object
        download_dir: Directory to save the download
        file_name: Name of the file to save (default: comtec_export.csv)
    """
    logging.info(f"Attempting to download Comtec report as {file_name}")

    export_button = page.get_by_role("button", name="Export")
    export_button.wait_for(state='visible', timeout=10000)
    export_button.click()

    logging.info("Waiting for download to complete...")

    with page.expect_download() as download_info:
        page.wait_for_timeout(1000)  
    download = download_info.value
    save_path = os.path.join(download_dir, file_name)
    download.save_as(save_path)

    logging.info(f"File downloaded successfully as {file_name}")
    
    
# ===========================
# Date and Time Utilities
# ===========================

def calculate_dates():
    """Calculate the current date in Chicago timezone and return the abbreviated month name."""
    chicago_tz = pytz.timezone('America/Chicago')
    month = datetime.now(chicago_tz).strftime('%b')
    day = datetime.now(chicago_tz).day
    today = month, day
    return today

def calculate_weekly_dates():
    """Calculate the start and end dates for the current week (Saturday to Friday)."""
    today = datetime.now()
    days_since_saturday = (today.weekday() + 2) % 7  # Saturday is 5
    last_saturday = today - timedelta(days=days_since_saturday)
    next_friday = last_saturday + timedelta(days=6)  # Friday is 6 days after Saturday

    start_date = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = next_friday.replace(hour=23, minute=59, second=59, microsecond=999999)

    return {
        "week": {
            "start": start_date,
            "end": end_date
        }
    }

def format_yesterday_today_range():
    """Format the date range from yesterday at 12:00 AM to today at 11:59 PM."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    formatted_start = start_time.strftime("%m/%d/%Y 12:00 am")
    formatted_end = end_time.strftime("%m/%d/%Y 11:59 pm")

    return f"{formatted_start} — {formatted_end}"

def call_on_fridays(function):
    """Decorator to call a function only on Fridays."""
    def wrapper(*args, **kwargs):
        if datetime.now().weekday() != 4:  # 4 is Friday
            logging.info("Skipping execution; this function can only run on Fridays.")
            return
        return function(*args, **kwargs)    
    return wrapper



def daily_call_date_range():
    """Get the date range based on current day and time in EST."""
    est = pytz.timezone('America/New_York')
    now = datetime.now(est)
    weekday = now.weekday()  # 0=Monday through 6=Sunday
    current_time = now.time()

    # Monday AM Rule
    if weekday == 0 and (current_time.hour < 11 or (current_time.hour == 11 and current_time.minute <= 30)):
        start_date = now - timedelta(days=3)  # Go back to Friday
        start_date = start_date.replace(hour=11, minute=30)
        end_date = now.replace(hour=11, minute=29)
    
    # Tuesday through Thursday AM Rule
    elif weekday in [1, 2, 3] and (current_time.hour < 11 or (current_time.hour == 11 and current_time.minute <= 30)):
        start_date = (now - timedelta(days=1)).replace(hour=15, minute=30)
        end_date = now.replace(hour=11, minute=29)
    
    # Monday through Thursday PM Rule
    elif weekday in [0, 1, 2, 3] and current_time.hour >= 15 and current_time.minute >= 30:
        start_date = now.replace(hour=11, minute=30)
        end_date = now.replace(hour=15, minute=29)
    
    # Friday AM Rule
    elif weekday == 4 and current_time.hour < 11:
        start_date = (now - timedelta(days=1)).replace(hour=15, minute=30)
        end_date = now.replace(hour=11, minute=29)
    
    # Default case (1 day and 15 min before now)
    else:
        end_date = now
        start_date = end_date - timedelta(days=1, minutes=15)

    # Format dates in EST
    From = start_date.strftime('%m/%d/%Y %I:%M %p')
    To = end_date.strftime('%m/%d/%Y %I:%M %p')

    return From, To

# ===========================
# Text Input Utilities
# ===========================

def fill_with_delay(page, selector, text, delay=50):
    """Type text into an element with a delay between each character."""
    for char in text:
        page.locator(selector).type(char, delay=delay)

def retry_operation(operation, attempts=5, delay=60, *args, **kwargs):
    """Retries a given operation with a specified delay between attempts."""
    for attempt in range(attempts):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < attempts - 1:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    raise Exception(f"All {attempts} attempts failed.")