import os
from helper import *
from activity import *

def main():
    try:
        # Production Google Sheet IDs
        call_reporting = os.getenv('CALL_REPORT_SHEET_ID')
        
        #Daily Call Comtech Report
        logging.info('Daily Abonded Calls Reporting')
        browser, playwright, page = launch_browser(headless=True)
        daily_call_comtech_report(page,browser,playwright)
        daily_abonded_download = os.path.join(download_dir, 'daily_abonded_calls.csv')
        google_data_upload(daily_abonded_download,'Data',call_reporting)
        logging.info('Daily Abonded Call Reporting Complete')
        
    except Exception as e:
        logging.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    main()