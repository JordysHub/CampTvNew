# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings
import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.dictionaries as dict
from camp_tv_new.src.utils.logger import setup_logger, timer_func

from dotenv import load_dotenv
import pandas as pd
import time
from tqdm import tqdm
import warnings
import os

# pd.set_option('future.no_silent_downcasting', True)
# warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
# warnings.simplefilter(action='ignore', category=FutureWarning)
# endregion

# Load environment variables
load_dotenv()
# setup logger
logger = setup_logger()

@timer_func
def get_bereik(df_flights, target_group: str) -> pd.DataFrame:

    df_bereik = pd.DataFrame()
    current_token_time = time.time()  # Get current time when starting
    token = api_utils.get_api_token()  # Fetch initial token

    for _, row in tqdm(df_flights.iterrows(), total=len(df_flights), position=0, ncols=120,
                       desc=f"Processing flights for target group {target_group}",
                       bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):

        if time.time() - current_token_time >= 3000:
            logger.debug("Refreshing token...")
            token = api_utils.get_api_token()
            current_token_time = time.time()

        df = bereik_utils.get_bereik(row.name, row, target_group, token)
        df_bereik = pd.concat([df_bereik, df], ignore_index=True)

    return df_bereik
@timer_func
def process_target_group(target_group: str, df_all_flights: pd.DataFrame) -> None:
    """
    Process data for a specific target group.
    """
    folder_path_bereik = os.getenv("raw_bereik_folder")
    directory_raw = f"{folder_path_bereik}{target_group}/"
    os.makedirs(directory_raw, exist_ok=True)
    file_path = os.path.join(directory_raw, f"{target_group}_bereik_all_flights.xlsx")

    if not os.path.exists(file_path):
        logger.info(f"Fetching all data for new target group {target_group}...")
        try:
            df_bereik = get_bereik(df_all_flights, target_group)
            df_bereik.to_excel(file_path, index=False)  
            return     
        
        except Exception as e:
            logger.error(f"Error fetching data for new target group {target_group}: {str(e)}")

    df_bereik_old = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})

    list_of_flights, extra_flights_in_df = bereik_utils.get_new_and_updated_flights(df_bereik_old, df_all_flights)
    df_flights_to_get = df_all_flights[df_all_flights['flight_id'].isin(list_of_flights)]

    df_old_filtered = df_bereik_old[~df_bereik_old['flight_id'].isin(list_of_flights)]
    df_old_filtered = df_old_filtered[~df_old_filtered['flight_id'].isin(extra_flights_in_df)]

    df_bereik_new = get_bereik(df_flights_to_get, target_group)

    df_combined = pd.concat([df_old_filtered, df_bereik_new], ignore_index=True)
    
    try:
        assert set(df_combined['flight_id']) == set(df_all_flights['flight_id'])
    except AssertionError:
        print("Warning: The flight_id sets do not match.")
        combined_set = set(df_combined['flight_id'])
        all_flights_set = set(df_all_flights['flight_id'])

        missing_in_combined = all_flights_set - combined_set
        missing_in_all_flights = combined_set - all_flights_set
        logger.info(f"Missing flights in combined set: {missing_in_combined}")
        logger.info(f"Missing flights in all flights set: {missing_in_all_flights}")
        
    df_combined.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)
    df_combined.to_excel(file_path, index=False)
    logger.info(f"Saved updated and new data for target group {target_group} at {file_path}")
    
@timer_func
def process_file(file_path, parent_folder):
    """
    Process a single file by updating the flight_id for each row of data.
    Args:
        file_path (str): Path to the file.
    """
    bereik_processed_folder = os.getenv("bereik_processed_folder")
    # Read the file and process each row
    df = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})
    processed_rows = [bereik_utils.process_row(row) for _, row in df.iterrows()]
    processed_df = pd.DataFrame(processed_rows).fillna(0)
    # change column order
    processed_df = bereik_utils.change_column_order(processed_df)
    # Write the updated DataFrame back to the Excel file
    output_file_path = os.path.join(bereik_processed_folder, parent_folder, os.path.basename(file_path))
    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    # Save the DataFrame to Excel
    processed_df.to_excel(output_file_path, index=False)

def process_directory(directory_path):
    """
    Process all files in a directory and its subdirectories.
    Args:
        directory_path (str): Path to the directory.
    """
    total_files = sum(len(files) for _, _, files in os.walk(directory_path))
    with tqdm(total=total_files, desc="Processing Files") as pbar_files:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.xlsx'):
                    file_path = os.path.join(root, file)
                    parent_folder = os.path.basename(os.path.dirname(file_path))
                    process_file(file_path, parent_folder)
                    pbar_files.update(1)  # Update progress bar for each file processed

@timer_func
def main():
    """	
    This function fetches raw bereik for all target groups in the dict. It will fetch all the flights from the all flights file.
    The raw data is saved first and then processed to a better format.
    """

    logger.info("Starting data processing for flights...")

    all_flights_path = os.getenv("all_flights_path")
    df_all_flights = pd.read_excel(all_flights_path, dtype={'start_date': str, 'end_date': str}, usecols=range(5))

    total_target_groups = len(dict.target_groups)
    processed_target_groups = 0

    for target_group in [ '25-67', '68+', '35-59']:
        processed_target_groups += 1
        logger.info(f"Processing target group {target_group} ({processed_target_groups}/{total_target_groups})")
        process_target_group(target_group, df_all_flights)

    logger.info("Raw bereik fetched for all flights")
    logger.info("Process raw bereik...")

    raw_bereik_folder = os.getenv("raw_bereik_folder") 
    process_directory(raw_bereik_folder)

    logger.info("Bereik processed for all target groups")

if __name__ == "__main__":
    main()
