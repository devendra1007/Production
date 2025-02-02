import csv
import os   
from helper import *
import pandas as pd


# ===========================
# ECW
# ===========================

def daily_pro_orders(page,browser,playwright):
    try:
        logging.info("Starting daily_pro_orders")
        page.goto(os.getenv("ECW_URL"))
        wait_for_page_load(page)
        fill_with_delay(page, 'input#username', os.getenv("ECW_USERNAME"))
        fill_with_delay(page, 'input#password', os.getenv("ECW_PASSWORD"))
        page.get_by_role("button", name="Login").click()
        logging.info("Logged in successfully")
        page.get_by_role("link", name="Dashboard", exact=True).click()
        page.get_by_role("link", name="Shortcut to Pro Orders with Ins RS", exact=True).click()
        page.wait_for_load_state('networkidle',timeout=120000)
        page.wait_for_selector('img[title="Run Report"]', timeout=60000)
        retry_operation(page.get_by_label("Run Report").click)
        wait_for_page_load(page,timeout=90000)
        logging.info("Report run successfully")
        page.get_by_label("Date Selection").select_option("Custom Date", timeout=30000)
        page.get_by_label("Text box prompt").click(timeout=30000)
        page.get_by_label("Text box prompt").fill("0", timeout=30000)               
        page.locator("input[aria-label='Year entry text field']").first.wait_for(state="visible", timeout=30000)
        page.locator("input[aria-label='Year entry text field']").first.evaluate("element => element.value = ''")  # Clear the field first
        page.locator("input[aria-label='Year entry text field']").first.fill("2024", timeout=30000)
        page.locator("input[aria-label='Year entry text field']").first.press("Enter")
        page.wait_for_timeout(5000)
        page.get_by_role("option", name="Jun", exact=True).first.click(timeout=30000)
        page.get_by_role("option", name="1", exact=True).first.click(timeout=30000)
        page.get_by_role("option", name=str(calculate_dates()[0]), exact=True).nth(1).click(timeout=30000)
        page.get_by_role("option", name=str(calculate_dates()[1]), exact=True).nth(1).click(timeout=30000)
        page.get_by_role("button", name="OK").click()
        wait_for_page_load(page,timeout=90000)
        logging.info("Date selected successfully")
        page.get_by_label("Keywords:").first.click()
        page.get_by_label("Keywords:").fill("ord")
        page.get_by_role("button", name="Search").click()
        page.get_by_role("link", name="Select all", exact=True).nth(1).click()
        page.get_by_role("button", name="InsertAdd selected items to").click()
        listbox = page.locator("select[multiple]").first
        options = [
            "", "*Auth Denied", "*Auth Submitted", "*Declined", "*Done", "*Duplicate",
            "*Info updated", "*Lock Note", "*Missing Info", "*Peer to Peer",
            "*Pending Auth", "*Pending Estimate", "*PT/Imaging Needed",
            "*Ready to Schedule", "*Ready To Schedule BT", "*Ready To Schedule PC"
        ]

        for option in options:
            try:
                option_element = listbox.locator(f"option:has-text('{option}')").first
                if option_element.is_visible():  # Check if the option is visible
                    option_element.click(modifiers=['Control'])
                    page.wait_for_timeout(100)
                else:
                    logging.info(f"Option '{option}' not found, skipping.")
            except Exception as e:
                logging.warning(f"Failed to select option '{option}': {str(e)}")

        page.get_by_role("button", name="Finish").click()
        wait_for_page_load(page,timeout=120000)
        logging.info("Report finished successfully")
        retry_operation(change_report_format_and_download, page=page, download_dir=download_dir, file_name='daily_pro_orders')
        logging.info("Report downloaded successfully")
        page.get_by_label("Log Off").click()
        wait_for_page_load(page,timeout=120000)
        page.close()
        logging.info("daily_pro_orders completed successfully")
    except Exception as e:
        logging.error(f"Error in daily_pro_orders: {e}")
    finally:
        browser.close()
        playwright.stop()

 
 
def dme_orders(page,browser,playwright):
    try:
        page.goto(os.getenv("ECW_URL"))
        wait_for_page_load(page)
        fill_with_delay(page, 'input#username', os.getenv("ECW_USERNAME"))
        fill_with_delay(page, 'input#password', os.getenv("ECW_PASSWORD"))
        logging.info("Logged in successfully")
        page.get_by_role("button", name="Login").click()
        page.get_by_role("link", name="Dashboard", exact=True).click()
        page.get_by_role("link", name="Report View of 4.14 - Next Day Appointments", exact=True).click()
        page.wait_for_load_state('networkidle',timeout=120000)
        page.wait_for_selector('img[title="Run Report"]', timeout=60000)
        retry_operation(page.get_by_label("Run Report").click)
        wait_for_page_load(page,timeout=90000)
        logging.info("Report run successfully")
        retry_operation(change_report_format_and_download, page=page, download_dir=download_dir, file_name='dme_orders')
        logging.info("Report downloaded successfully")
        page.get_by_label("Log Off").click()
        wait_for_page_load(page,timeout=120000)
        page.close()
        logging.info("dme_orders completed successfully")
    except Exception as e:
        logging.error(f"Error in dme_orders: {e}")
    finally:
        browser.close()
        playwright.stop()



# ===========================
# COMTEC
# ===========================

def daily_call_comtech_report(page,browser,playwright):
    try:
        logging.info("Starting daily_call_comtech_report")
        page.goto(os.getenv("COMTEC_URL"))
        wait_for_page_load(page)
        fill_with_delay(page, 'input[placeholder="Login Name"]', os.getenv("COMTEC_USERNAME"))
        fill_with_delay(page, 'input[placeholder="Password"]', os.getenv("COMTEC_PASSWORD"))
        page.get_by_role("button", name="Log In").click()
        page.get_by_role("link", name="Reporting").click()
        page.get_by_role("link", name="Filters").click()
        from_date, to_date = daily_call_date_range()
        # Clear old value and set the new date for the 'from' field
        page.locator("body").click() 
        page.wait_for_timeout(1000)
        page.locator("#from-0").fill("")
        page.locator("#from-0").click()
        page.keyboard.type(from_date, delay=100)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.keyboard.press("Escape")  
        page.wait_for_timeout(500)
        # Clear old value and set the new date for the 'to' field
        page.locator("input[name=\"data\\[callhistory\\]\\[to\\]\"]").fill("")
        page.locator("input[name=\"data\\[callhistory\\]\\[to\\]\"]").click()
        page.keyboard.type(to_date, delay=100)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.keyboard.press("Escape")  
        page.wait_for_timeout(500)
        page.locator("#callhistoryCallType").select_option("Missed")
        page.get_by_role("button", name="Filter").click()
        page.wait_for_timeout(5000)
        retry_operation(download_comtec_report, page=page, download_dir=download_dir, file_name='daily_abonded_calls.csv')
        page.get_by_text("Sahil Thorat (1011)").click()
        page.get_by_role("link", name="Log Out").click()
        page.close()
        logging.info("daily_call_comtech_report completed successfully")
    except Exception as e:
        logging.error(f"Error in daily_call_comtech_report: {e}")
    finally:
        browser.close()
        playwright.stop()
        

# ===========================
# Google Sheet Upload
# ===========================
def google_data_upload(download_path, sheet_name, spreadsheet_id, encoding='utf-8',delimiter=','):
    try:
        credentials = get_user_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Read data from the CSV file with the correct encoding
        with open(download_path, 'r', encoding=encoding) as file:  # Adjust encoding if needed
            csv_reader = csv.reader(file, delimiter=delimiter)
            csv_data = list(csv_reader)

        # Retrieve the sheet ID for the given sheet name
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId")
                break

        if sheet_id is None:
            raise ValueError(f"Sheet with name '{sheet_name}' not found.")

        # Clear existing data in the sheet using batchUpdate
        requests = [{
            'updateCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'startColumnIndex': 0
                },
                'fields': 'userEnteredValue'
            }
        }]
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        # Append new data to the sheet
        range_name = f'{sheet_name}!A1'  # Adjust the starting cell as needed
        body = {
            'values': csv_data
        }
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='OVERWRITE',
            body=body
        ).execute()

        logging.info("Data uploaded successfully to Google Sheet.")
        
    except Exception as e:
        logging.error(f"Error uploading data to Google: {e}")