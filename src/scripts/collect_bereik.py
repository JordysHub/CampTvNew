# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
from camp_tv_new.src.utils.query_dict import query_dict
import camp_tv_new.src.utils.dictionaries as mydict

import pandas as pd
import time
from tqdm import tqdm
import argparse

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
def get_bereik(df_missing_flights):
    """
    Fetch bereik data for the given flights and target group(s).
    """
    current_token_time = time.time()
    token = api_utils.get_api_token()

    for idx, row in tqdm(df_missing_flights.iterrows(), total=len(df_flights), position=0, ncols=120,
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

def retrieve_and_format_flights(query_key):
    df = db_utils.query_to_df(query_dict[query_key])
    df['start_date'] = pd.to_datetime(df['start_date']).dt.strftime("%d%m%y")
    df['end_date'] = pd.to_datetime(df['end_date']).dt.strftime("%d%m%y")
    return df

def retrieve_missing_flights_per_target_group(df_flights, existing_campaign_data, target_groups):
    all_combinations = pd.MultiIndex.from_product([df_flights['flight_id'], target_groups], names=['flight_id', 'target_group']).to_frame(index=False)
    missing_pairs = all_combinations.merge(existing_campaign_data, on=['flight_id', 'target_group'], how='left', indicator=True)
    missing_pairs = missing_pairs[missing_pairs['_merge'] == 'left_only'].drop(columns=['_merge'])
    grouped_df = missing_pairs.groupby('flight_id')['target_group'].apply(lambda x: ', '.join(x)).reset_index()
    grouped_df.columns = ['flight_id', 'missing_target_groups']
    df_missing_flights = df_flights.merge(grouped_df, on='flight_id', how='left')
    df_missing_flights = df_missing_flights.dropna(subset=['missing_target_groups'])

    return df_missing_flights

if __name__ == "__main__":
    # Step 1: Retrieve flights data and format dates. Retrieve existing data in bereik table
    df_flights = retrieve_and_format_flights('get_flights')
    existing_campaign_data = db_utils.query_to_df(query_dict['get_existing_campaign_data'])

    # Step 2: Parse command line arguments
    args = parse_arguments()
    target_groups = args.tg if args.tg else mydict.target_groups

    # Step 3: Get all missing target_groups for every flight_id
    df_missing_flights = retrieve_missing_flights_per_target_group(df_flights, existing_campaign_data, target_groups)

    # Step 4: Retrieve missing flights for each target group and process
    if df_missing_flights is not None and not df_missing_flights.empty:
        logger.debug(f"Retrieving {len(df_missing_flights)} missing flights for {len(target_groups)} target groups...")
        get_bereik(df_missing_flights)

    # # Step 5: Retrieve flights with duration mismatch that need to be updated
    # df_duration_mismatch = db_utils.query_to_df(query_dict['get_flights_with_duration_mismatch'])
    # if df_duration_mismatch is not None and not df_missing_flights.empty:
    #     update_running_flights(df_flights, target_groups)
