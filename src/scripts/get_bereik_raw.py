# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings
import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.dictionaries as dict

from dotenv import load_dotenv
from camp_tv_new.src.utils.logger import setup_logger, timer_func

import pandas as pd
import time
from tqdm import tqdm
import warnings
import os

pd.set_option('future.no_silent_downcasting', True)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
# endregion

# Load environment variables: determines whether to retrieve data exclusively from Ster/NPO.
load_dotenv()
# setup logger
logger = setup_logger()

@timer_func
def get_bereik(df_flights, target_group: str) -> pd.DataFrame:
    """
    """
    df_bereik = pd.DataFrame()
    current_token_time = time.time()  # Get current time when starting
    token = api_utils.get_api_token()  # Fetch initial token

    for _, row in tqdm(df_flights.iterrows(), total=len(df_flights), position=0, ncols=120,
                       desc=f"Processing flights for target group {target_group}",
                       bar_format = "{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):

        if time.time() - current_token_time >= 3000:
            logger.debug("Refreshing token...")
            token = api_utils.get_api_token()
            current_token_time = time.time()  
        df = bereik_utils.get_bereik(row.name, row, target_group, token)
        df_bereik = pd.concat([df_bereik, df], ignore_index=True)

    return df_bereik

def main():
    """
    Main function to process data based on command line arguments.
    """
    logger.info("Starting data processing for flights...")

    df_flights_updated = pd.read_excel("./data/interim/flights/all_flights_updated.xlsx", dtype={'start_date': str, 'end_date': str})
    df_flights_new = pd.read_excel("./data/interim/flights/all_flights_new.xlsx", dtype={'start_date': str, 'end_date': str})
    df_all_flights = pd.read_excel("./data/interim/flights/all_flights.xlsx", dtype={'start_date': str, 'end_date': str})

    total_target_groups = len(dict.target_groups)
    processed_target_groups = 0

    for target_group in dict.target_groups:
        processed_target_groups += 1
        directory_raw = f"./data/raw/api/bereik/{target_group}/"
        os.makedirs(directory_raw, exist_ok=True)

        filepath = os.path.join(directory_raw, f"{target_group}_bereik_all_flights.xlsx")

        # Fetch data only if the target group folder didn't exist yet
        if not os.path.exists(filepath):
            try:
                logger.info(f"Fetching all data for new target group {target_group}")
                df_bereik = get_bereik(df_all_flights, target_group)
                df_bereik.to_excel(filepath, index=False)
            except Exception as e:
                logger.error(f"Error fetching data for new target group {target_group}: {str(e)}")
                continue

        # Perform data processing for the current target group
        try:
            logger.info(f"Processing data for target group {target_group} ({processed_target_groups}/{total_target_groups})...")

            df_bereik_old = pd.read_excel(filepath, dtype={'start_date': str, 'end_date': str})
            # remove updated flights from old bereik data
            df_bereik_old = df_bereik_old[~df_bereik_old['flight_id'].isin(df_flights_updated['flight_id'])]

            # Fetch data for updated and new flights and merge with the existing data
            logger.debug("Updating flights....")
            df_bereik_updated = get_bereik(df_flights_updated, target_group)
            logger.debug("Fetching new flights...")
            df_bereik_new = get_bereik(df_flights_new, target_group)

            df_combined = pd.concat([df_bereik_old, df_bereik_updated, df_bereik_new], ignore_index=True)

            # Sort the combined DataFrame by specified columns
            df_combined.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)
            df_combined.to_excel(filepath, index=False)
            logger.info(f"Saved updated and new data for target group {target_group} at {filepath}")

        except Exception as e:
            logger.error(f"Error processing data for target group {target_group}: {str(e)}")

    logger.info("Data processing for flights completed.")

if __name__ == "__main__":
    main()
