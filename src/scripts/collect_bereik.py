# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import time
from tqdm import tqdm
import warnings
import os
import argparse

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.dictionaries as dict
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.dictionaries as mydict

# pd.set_option('future.no_silent_downcasting', True)
# warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

# Setup logger
logger = setup_logger()

def parse_arguments():
    """
    Parse command line arguments and return the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Get target_group data.")
    parser.add_argument(
        "--tg",
        type = list,
        default = mydict.target_groups,
        help="List of target groups to process.",
    )
    return parser.parse_args()

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

def process_target_group(folder_path_bereik: str, target_group: str, df_all_flights: pd.DataFrame) -> None:
    """
    Process data for a specific target group.
    """
    
    directory_raw = f"{folder_path_bereik}{target_group}/"
    os.makedirs(directory_raw, exist_ok=True)
    file_path = os.path.join(directory_raw, f"{target_group}_bereik_all_flights.xlsx")

    if not os.path.exists(file_path):
        logger.info(f"Collecting all data for new target group {target_group}...")
        try:
            df_bereik = get_bereik(df_all_flights, target_group)
            df_bereik.to_excel(file_path, index=False)  
        except Exception as e:
            logger.error(f"Error collecting data for new target group {target_group}: {str(e)}")
        return

    df_bereik_old = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})
    list_of_flights, extra_flights_in_df = bereik_utils.get_new_and_updated_flights(df_bereik_old, df_all_flights)
    df_flights_to_get = df_all_flights[df_all_flights['flight_id'].isin(list_of_flights)]

    df_old_filtered = df_bereik_old[~df_bereik_old['flight_id'].isin(list_of_flights)]
    df_old_filtered = df_old_filtered[~df_old_filtered['flight_id'].isin(extra_flights_in_df)]
    df_bereik_new = get_bereik(df_flights_to_get, target_group)
    df_combined = pd.concat([df_old_filtered, df_bereik_new], ignore_index=True)
    
    # do a check if flights match
    if set(df_combined['flight_id']) != set(df_all_flights['flight_id']):
        logger.warning("The flight_id sets do not match.")
        combined_set = set(df_combined['flight_id'])
        all_flights_set = set(df_all_flights['flight_id'])
        
        missing_in_combined = all_flights_set - combined_set
        missing_in_all_flights = combined_set - all_flights_set
        logger.info(f"Missing flights in combined set: {missing_in_combined}")
        logger.info(f"Missing flights in all flights set: {missing_in_all_flights}")
        
    df_combined.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)
    df_combined.to_excel(file_path, index=False)
    logger.info(f"Saved updated and new data for target group {target_group} at {file_path}")
    
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    args = parse_arguments()
    
    all_flights_path = os.getenv("all_flights_path")
    folder_path_bereik = os.getenv("raw_bereik_folder")
    df_all_flights = pd.read_excel(all_flights_path, dtype={'start_date': str, 'end_date': str}, usecols=range(5))
    
    total_target_groups = len(dict.target_groups)
    for i, target_group in enumerate(args.tg, start=1):
        logger.info(f"Processing target group {target_group} ({i}/{total_target_groups})")
        process_target_group(folder_path_bereik, target_group, df_all_flights)
        
    logger.info("Raw bereik collected for all flights")
