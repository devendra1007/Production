import os
from helper import *
from activity import *

def main():
    try:
        
        # Production Google Sheet IDs
        daily_pro_orders_sheet_id = os.getenv('DAILY_PRO_ORDERS_SPREADSHEET_ID')
        dme_sheet_id = os.getenv('DME_SPREADSHEET_ID')
             
        #Daily Pro Orders
        logging.info('Daily Pro Orders')
        browser, playwright, page = launch_browser(headless=True)
        daily_pro_orders(page,browser,playwright)
        daily_pro_orders_download = os.path.join(download_dir, 'daily_pro_orders.csv')
        google_data_upload(daily_pro_orders_download,'Main',daily_pro_orders_sheet_id,encoding='utf-16',delimiter='\t')
        google_data_upload(daily_pro_orders_download,'PS',dme_sheet_id,encoding='utf-16',delimiter='\t')
        logging.info('Daily Pro Orders Complete')
        
        #DME Orders
        logging.info('DME Orders')
        browser, playwright, page = launch_browser(headless=True)
        dme_orders(page,browser,playwright)
        dme_orders_download = os.path.join(download_dir, 'dme_orders.csv')
        google_data_upload(dme_orders_download,'DR',dme_sheet_id,delimiter='\t',encoding='utf-16')
        logging.info('DME Orders Complete')
        
        
    except Exception as e:
        logging.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    main()