# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.dictionaries as dict
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.dictionaries as mydict

import pandas as pd
import time
from tqdm import tqdm
import warnings
import os
import argparse
import time
import random

# pd.set_option('future.no_silent_downcasting', True)
# warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
# warnings.simplefilter(action='ignore', category=FutureWarning)

COLLECT_MOCKS = True

# Setup logger
logger = setup_logger()

def parse_arguments():
    """
    Parse command line arguments and return the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Get target_group data.")
    parser.add_argument(
        "--tg",
        type = str,
        nargs='+',  # Allows one or more values to be provided for the --tg argument
        default = mydict.target_groups,
        help="List of target groups to process.",
    )
    return parser.parse_args()

def retry_with_exponential_backoff(func, *args, retries=5, initial_wait=1, max_wait=60, **kwargs):
    """
    Retry a function with exponential backoff.

    Parameters:
        func (callable): The function to be retried.
        retries (int): Number of retries.
        initial_wait (int): Initial wait time between retries.
        max_wait (int): Maximum wait time between retries.
    """
    wait = initial_wait
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                raise
            time.sleep(wait)
            wait = min(wait * 2, max_wait)

@timer_func
def get_bereik(df_flights, target_group: str, file_path) -> pd.DataFrame:
    """
    Fetch bereik data for the given flights and target group.
    """
    all_flights_path = str(os.getenv("all_flights_path"))
    df_bereik = pd.DataFrame()
    current_token_time = time.time()
    token = api_utils.get_api_token()
    rows_to_remove = []

    for idx, row in tqdm(df_flights.iterrows(), total=len(df_flights), position=0, ncols=120,
                       desc=f"Processing flights for target group {target_group}",
                       bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):
        
        if time.time() - current_token_time >= 3000:
            logger.debug("Refreshing token...")
            token = api_utils.get_api_token()
            current_token_time = time.time()

        def fetch_bereik():
            return bereik_utils.get_bereik(row.name, row, target_group, token)

        try:
            # Retry fetching bereik for the current row if an error occurs
            df = retry_with_exponential_backoff(fetch_bereik)
            if not df.empty:
                df_bereik = pd.concat([df_bereik, df], ignore_index=True)
            else:
                # Add index to rows_to_remove if df is empty (campaign doesnt exist or has changed)
                rows_to_remove.append(idx)
        except Exception as e:
            # Log error and continue with the next row
            df_bereik.to_excel(f"{file_path}_uncomplete.xlsx", index=False)
            logger.error(f"Error fetching bereik for flight {row.name}: {str(e)}")
    
    # Remove rows from df_flights
    df_flights.drop(rows_to_remove, inplace=True)
    df_flights.reset_index(drop=True, inplace=True)  # Reset index after dropping rows
    df_flights.to_excel(all_flights_path, index=False)
    logger.info(f"Deleted {len(rows_to_remove)} rows from df_all_flights")

    return df_bereik

def fetch_and_save_new_data(file_path: str, target_group: str, df_all_flights: pd.DataFrame) -> None:
    """
    Fetch and save new data for a target group.
    """
    logger.info(f"Collecting all data for new target group {target_group}...")
    try:
        df_bereik = get_bereik(df_all_flights, target_group, file_path)
        df_bereik.to_excel(file_path, index=False)
        logger.info(f"Saved new data for target group {target_group} at {file_path}")
    except Exception as e:
        logger.error(f"Error collecting data for new target group {target_group}: {str(e)}")

def update_existing_data(file_path: str, target_group: str, df_all_flights: pd.DataFrame) -> None:
    """
    Update existing data for a target group.
    """
    logger.info(f"Updating existing data for target group {target_group}...")
    try:
        df_bereik_old = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})
        list_of_flights, extra_flights_in_df = bereik_utils.get_new_and_updated_flights(df_bereik_old, df_all_flights)
        df_flights_to_get = df_all_flights[df_all_flights['flight_id'].isin(list_of_flights)]

        df_old_filtered = df_bereik_old[~df_bereik_old['flight_id'].isin(list_of_flights)]
        df_old_filtered = df_old_filtered[~df_old_filtered['flight_id'].isin(extra_flights_in_df)]
        df_bereik_new = get_bereik(df_flights_to_get, target_group)
        df_combined = pd.concat([df_old_filtered, df_bereik_new], ignore_index=True)

        validate_data_integrity(df_combined, df_all_flights)

        df_combined.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)
        df_combined.to_excel(file_path, index=False)
        logger.info(f"Saved updated and new data for target group {target_group} at {file_path}")
    except Exception as e:
        logger.error(f"Error updating data for target group {target_group}: {str(e)}")

def validate_data_integrity(df_combined: pd.DataFrame, df_all_flights: pd.DataFrame) -> None:
    """
    Validate the integrity of the combined data.
    """
    if set(df_combined['flight_id']) != set(df_all_flights['flight_id']):
        logger.warning("The flight_id sets do not match.")
        combined_set = set(df_combined['flight_id'])
        all_flights_set = set(df_all_flights['flight_id'])

        missing_in_combined = all_flights_set - combined_set
        missing_in_all_flights = combined_set - all_flights_set
        logger.info(f"Missing flights in combined set: {missing_in_combined}")
        logger.info(f"Missing flights in all flights set: {missing_in_all_flights}")

def process_target_group(raw_bereik_folder: str, target_group: str, df_all_flights: pd.DataFrame, is_mock: bool = False) -> None:
    """
    Process data for a specific target group.
    """
    # Create a subdirectory for mock campaigns if is_mock is True
    subdir = 'mock_campaigns' if is_mock else ''
    directory_raw = os.path.join(raw_bereik_folder, target_group, subdir)
    os.makedirs(directory_raw, exist_ok=True)

    # Adjust the filename to include 'mock' if is_mock is True
    filename_suffix = '_mock' if is_mock else ''
    file_path = os.path.join(directory_raw, f"{target_group}_bereik_all_flights{filename_suffix}.xlsx")

    if not os.path.exists(file_path):
        print('Raw bereik folder does not exist. Creating...')
        fetch_and_save_new_data(file_path, target_group, df_all_flights)
    else:
        print(f'Raw bereik folder for target group {target_group} already exists. Updating...')
        update_existing_data(file_path, target_group, df_all_flights)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    args = parse_arguments()

    all_flights_path = str(os.getenv("all_flights_path"))
    all_mocks_path = str(os.getenv("all_mocks_path"))
    raw_bereik_folder = str(os.getenv("raw_bereik_folder"))
    df_all_flights = pd.read_excel(all_flights_path, dtype={'start_date': str, 'end_date': str}, usecols=range(5))
    

    total_target_groups = len(args.tg)
    for i, target_group in enumerate(args.tg, start=1):
        logger.info(f"Processing target group {target_group} ({i}/{total_target_groups})")
        process_target_group(raw_bereik_folder, target_group, df_all_flights)
        
    if COLLECT_MOCKS:
        df_all_mocks = pd.read_excel(all_mocks_path, dtype={'start_date': str, 'end_date': str})
        for i, target_group in enumerate(args.tg, start=1):
            logger.info(f"Processing mock_campaigns for target group {target_group} ({i}/{total_target_groups})")
            process_target_group(raw_bereik_folder, target_group, df_all_mocks, is_mock=True)

    logger.info("Raw bereik collected for all flights")
