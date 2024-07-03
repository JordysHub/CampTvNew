# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.database_utils as db_utils
import camp_tv_new.src.utils.connection_utils as con_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.dictionaries as mydict

import pandas as pd
import time
from tqdm import tqdm
import os
import argparse
import time

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

@timer_func
def get_bereik(df_flights, target_group: str):
    """
    Fetch bereik data for the given flights and target group.
    """
    current_token_time = time.time()
    token = api_utils.get_api_token()

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
            # Fetch data, preprocess and dump to sql
            df = api_utils.retry_with_exponential_backoff(fetch_bereik)
            processed_df = bereik_utils.process_raw_bereik_data(df, target_group)
            db_utils.dump_to_sql(processed_df, 'tv.bereik')

        except Exception as e:
            logger.error(f"Error fetching bereik for flight {row.name}: {str(e)}")

def update_existing_data(target_group: str, df_all_flights: pd.DataFrame, bereik_data_tg: pd.DataFrame) -> None:
    """
    Update existing data for a target group.
    """
    try:
        # Step 1: Get flights that need to be updated and are new
        missing_flights_in_db, flights_to_update = bereik_utils.get_new_and_updated_flights(bereik_data_tg, df_all_flights)
        print(len(flights_to_update), len(missing_flights_in_db))

        # Step 2: Delete flights from db that need to be updated
        if len(flights_to_update) > 0:
            logger.info(f"Deleteting {len(flights_to_update)} flights from db to update")
            db_utils.delete_flights(flights_to_update, table_name = '[tv.bereik]')

        # Step 3: Get new flights for target group and update existing flights
        if len(missing_flights_in_db) > 0:
            logger.info(f"Getting {len(missing_flights_in_db)} new flights for target group {target_group}...")
            df_flights_to_get = df_all_flights[df_all_flights['flight_id'].isin(missing_flights_in_db)]
            get_bereik(df_flights_to_get, target_group)
        if len(flights_to_update) > 0:
            logger.info(f"Updating {len(flights_to_update)} flights for target group {target_group}...")
            df_flights_to_update = df_all_flights[df_all_flights['flight_id'].isin(flights_to_update)]
            get_bereik(df_flights_to_update, target_group)

    except Exception as e:
        logger.error(f"Error updating data for target group {target_group}: {str(e)}")

def process_target_group(target_group: str, df_all_flights: pd.DataFrame) -> None:
    """
    Process data for a specific target group.
    """
    query = f"""SELECT DISTINCT flight_id, target_group, campaign_duration FROM [dbo].[tv.bereik] where target_group = '{target_group}'"""
    bereik_data_tg = db_utils.query_to_df(query)

    if bereik_data_tg is None or bereik_data_tg.empty:
        logger.info(f"Collecting all data for new target group {target_group}...")
        try:
            get_bereik(df_all_flights, target_group)
        except Exception as e:
            logger.error(f"Error collecting data for new target group {target_group}: {str(e)}")
    else:
        logger.info(f"Updating flights for target group {target_group}...")
        update_existing_data(target_group, df_all_flights, bereik_data_tg)

if __name__ == "__main__":

    COLLECT_MOCKS = False
    args = parse_arguments()

    # Read the entire flights table into a DataFrame
    df_flights = db_utils.query_to_df('SELECT flight_id, advertiser, product, start_date, end_date, campaign_duration, mock_campaign FROM [dbo].[tv.flights]')
    # Change date format for the API
    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.strftime("%d%m%y")
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.strftime("%d%m%y")

    if not COLLECT_MOCKS:
        df_flights = df_flights[df_flights['mock_campaign'] == 0]

    total_target_groups = len(args.tg)
    for i, target_group in enumerate(args.tg, start=1):
        logger.info(f"Processing target group {target_group} ({i}/{total_target_groups})")
        process_target_group(target_group, df_flights)

    logger.info("Raw bereik collected for all flights")
