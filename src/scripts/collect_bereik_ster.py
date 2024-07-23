# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
from camp_tv_new.src.utils.query_dict import Queries
import camp_tv_new.src.utils.dictionaries as mydict

import pandas as pd
import time
from tqdm import tqdm
import argparse
import re

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

def rename_groups(s):
    # Define your renaming rules in a dictionary
    renaming_rules = mydict.rename_column_for_api

    # Replace according to the rules
    for old, new in renaming_rules.items():
        s = s.replace(old, new)
    return s

@timer_func
def get_bereik(df_missing_flights):
    """
    Fetch bereik data for the given flights and target group(s).
    """
    current_token_time = time.time()
    token = api_utils.get_api_token()

    for idx, row in tqdm(df_missing_flights.iterrows(), total=len(df_missing_flights), position=0, ncols=120,
                         desc=f"Processing missing flights for target groups",
                         bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):

        if time.time() - current_token_time >= 3000:
            logger.debug("Refreshing token...")
            token = api_utils.get_api_token()
            current_token_time = time.time()

        def fetch_bereik():
            return bereik_utils.get_bereik(row.name, row, token)

        try:
            # Fetch data, preprocess and dump to sql
            df = api_utils.retry_with_exponential_backoff(fetch_bereik)
            if df is not None and not df.empty:
                processed_df = bereik_utils.process_raw_bereik_data(df)
                db_utils.dump_to_sql(processed_df, 'tv.bereik_ster')

        except Exception as e:
            logger.error(f"Error fetching bereik for flight {row.name}: {str(e)}")

@timer_func
def process_missing_flights(target_groups):
    """Retrieve and process missing flights based on target groups."""
    # Get all missing flights for every target group
    df_missing_flights = db_utils.query_to_df(Queries.get_missing_flights_per_target_group(target_groups))

    if df_missing_flights is not None and not df_missing_flights.empty:
        logger.debug(f"Retrieving {len(df_missing_flights)} missing flights for {len(target_groups)} target groups...")

        # Process dates and target groups
        df_missing_flights['start_date'] = pd.to_datetime(df_missing_flights['start_date']).dt.strftime("%d%m%y")
        df_missing_flights['end_date'] = pd.to_datetime(df_missing_flights['end_date']).dt.strftime("%d%m%y")
        df_missing_flights['missing_target_groups'] = df_missing_flights['missing_target_groups'].apply(rename_groups)

        get_bereik(df_missing_flights)
    else:
        logger.debug("No missing flights found.")

@timer_func
def updates_flights(target_groups):
    """Retrieve, delete, and update flights with duration mismatch."""
    df_flights_mismatch = db_utils.query_to_df(Queries.get_mismatched_flights_per_target_group(target_groups))

    if df_flights_mismatch is not None and not df_flights_mismatch.empty:
        logger.debug(f"Deleting and updating {len(df_flights_mismatch)} flights for {len(target_groups)} target groups...")

        # Process dates and target groups
        df_flights_mismatch['start_date'] = pd.to_datetime(df_flights_mismatch['start_date']).dt.strftime("%d%m%y")
        df_flights_mismatch['end_date'] = pd.to_datetime(df_flights_mismatch['end_date']).dt.strftime("%d%m%y")
        df_flights_mismatch['missing_target_groups'] = df_flights_mismatch['missing_target_groups'].apply(rename_groups)

        # Delete mismatched flights
        flight_ids = df_flights_mismatch['flight_id'].tolist()
        db_utils.delete_flights(flight_ids, 'tv.bereik_ster', target_groups)

        get_bereik(df_flights_mismatch)
    else:
        logger.debug("No mismatches between flights.")

if __name__ == "__main__":
    # Step 1: Parse command line arguments
    args = parse_arguments()
    target_groups = args.tg if args.tg else mydict.target_groups

    # Step 2 & 3: Process missing flights
    process_missing_flights(target_groups)

    # Step 4: Process flights mismatch
    updates_flights(target_groups)