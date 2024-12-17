# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module collects data from the Bereik API and stores it in the database.
"""
import src.utils.bereik_utils as bereik_utils
import src.utils.api_utils as api_utils
import src.utils.database_utils as db_utils
from src.utils.logger import setup_logger, timer_func
from src.utils.query_dict import Queries
import src.utils.dictionaries as mydict

import pandas as pd
import time
from tqdm import tqdm
import argparse
import logging

# Setup logger
logger = setup_logger()


def parse_arguments():
    """
    Parse command line arguments and return the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Get target_group data.")
    parser.add_argument(
        "--tg",
        type=str,
        nargs="+",  # Allows one or more values to be provided for the --tg argument
        default=mydict.target_groups,
        help="List of target groups to process.",
    )
    return parser.parse_args()


@timer_func
def get_bereik(df_missing_flights):
    """
    Fetch bereik data for the given flights and target group(s).
    """
    current_token_time = time.time()
    token = api_utils.get_api_token()

    for _, row in tqdm(
        df_missing_flights.iterrows(),
        total=len(df_missing_flights),
        position=0,
        ncols=120,
        desc="Processing missing flights for target groups",
        bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}",
    ):

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
                db_utils.dump_to_sql(processed_df, "tv.bereik_ster")

        except Exception as e:
            logger.error("Error fetching bereik for flight %s: %s" % (row.name, str(e)))


@timer_func
def process_missing_flights(tgs):
    """Retrieve and process missing flights based on target groups."""
    # Get all missing flights for every target group
    logger.info("Get missing flights for target groups...")
    df_missing_flights = db_utils.query_to_df(Queries.get_missing_flights_per_target_group(tgs))

    if len(df_missing_flights) != 0:
        logger.info(f"Retrieving {len(df_missing_flights)} missing flights for {len(target_groups)} target groups...")
        # Process dates and target groups
        df_missing_flights["start_date"] = pd.to_datetime(df_missing_flights["start_date"]).dt.strftime("%d%m%y")
        df_missing_flights["end_date"] = pd.to_datetime(df_missing_flights["end_date"]).dt.strftime("%d%m%y")
        df_missing_flights["missing_target_groups"] = df_missing_flights["missing_target_groups"].apply(bereik_utils.rename_groups)
        get_bereik(df_missing_flights)
    else:
        logger.info("No missing flights found.")


if __name__ == "__main__":
    # Step 1: Parse command line arguments
    args = parse_arguments()
    target_groups = args.tg if args.tg else mydict.target_groups

    # Step 2: Process missing flights
    process_missing_flights(target_groups)
