# from google.cloud import bigquery
# from google.oauth2 import service_account
# import os
# from dotenv import load_dotenv
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Get base directory and load environment variables
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# load_dotenv(os.path.join(base_dir, '.env.test'))

# def load_csv_to_bigquery(csv_file_path):
#     try:
#         # Convert relative path to absolute path
#         if not os.path.isabs(csv_file_path):
#             csv_file_path = os.path.join(base_dir, csv_file_path.lstrip('../'))
        
#         # Validate CSV file exists
#         if not os.path.exists(csv_file_path):
#             raise FileNotFoundError(f"CSV file not found at {csv_file_path}")
        
#         # Get BigQuery credentials with debug logging
#         project_id = os.getenv("BQ_PROJECT_ID")
#         dataset_id = os.getenv("BQ_DATASET_ID")
#         table_name = os.getenv("BQ_TABLE_ID")
        
#         # Debug logging
#         logger.debug(f"Environment variables loaded:")
#         logger.debug(f"Project ID: {project_id}")
#         logger.debug(f"Dataset ID: {dataset_id}")
#         logger.debug(f"Table Name: {table_name}")
        
#         if not all([project_id, dataset_id, table_name]):
#             missing_vars = [var for var, val in {
#                 'BQ_PROJECT_ID': project_id,
#                 'BQ_DATASET_ID': dataset_id,
#                 'BQ_TABLE_NAME': table_name
#             }.items() if not val]
#             raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
#         table_id = f"{project_id}.{dataset_id}.{table_name}"
        
#         # Set up credentials
#         credentials_path = os.path.join(base_dir, 'config', 'credtest.json')
#         if not os.path.exists(credentials_path):
#             raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
        
#         credentials = service_account.Credentials.from_service_account_file(credentials_path)
#         client = bigquery.Client(project=project_id, credentials=credentials)
        
#         # Configure and execute load job
#         job_config = bigquery.LoadJobConfig(
#             source_format=bigquery.SourceFormat.CSV,
#             skip_leading_rows=1,
#             autodetect=True,
#             write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
#         )
        
#         logger.info(f"Loading CSV from: {csv_file_path}")
#         with open(csv_file_path, "rb") as source_file:
#             load_job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        
#         load_job.result()  # Wait for job completion
        
#         destination_table = client.get_table(table_id)
#         logger.info(f"Loaded {destination_table.num_rows} rows into {table_id}")
        
#     except Exception as e:
#         logger.error(f"Error loading CSV to BigQuery: {str(e)}")
#         raise

# if __name__ == "__main__":
#     csv_file_path = "downloads/sample.csv" 
#     load_csv_to_bigquery(csv_file_path)

