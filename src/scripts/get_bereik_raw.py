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


def main():

    logger.info("Starting data processing for flights...")

    df_all_flights = pd.read_excel("./data/interim/flights/all_flights.xlsx", dtype={'start_date': str, 'end_date': str}, usecols=range(5))

    total_target_groups = len(dict.target_groups)
    processed_target_groups = 0

    for target_group in dict.target_groups:
        processed_target_groups += 1
        directory_raw = f"./data/raw/api/bereik/{target_group}/"
        os.makedirs(directory_raw, exist_ok=True)
        file_path = os.path.join(directory_raw, f"{target_group}_bereik_all_flights.xlsx")

        # Fetch data only if the target group folder didn't exist yet
        if not os.path.exists(file_path):
            bereik_utils.fetch_all_data_new_tg(df_all_flights, target_group, file_path)

        # Fetch new flights and update old ones for the current target group
        logger.info(f"Processing data for target group {target_group} ({processed_target_groups}/{total_target_groups})...")
        df_bereik_old = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})
        # get new and updated flights
        list_of_flights = bereik_utils.get_new_and_updated_flights(df_bereik_old, df_all_flights)
        df_flights_to_get = df_all_flights[df_all_flights['flight_id'].isin(list_of_flights)]

        df_old_filtered = df_bereik_old[~df_bereik_old['flight_id'].isin(list_of_flights)]
        df_bereik_new = get_bereik(df_flights_to_get, target_group)

        # Sort the combined DataFrame by specified columns
        df_combined = pd.concat([df_old_filtered, df_bereik_new], ignore_index=True)
        df_combined.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)
        df_combined.to_excel(file_path, index=False)
        logger.info(f"Saved updated and new data for target group {target_group} at {file_path}")

    logger.info("Data processing for flights completed.")

if __name__ == "__main__":
    main()
