# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.dictionaries as mydict
from camp_tv_new.src.utils.query_dict import query_dict

import pandas as pd
import time
from tqdm import tqdm
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
            if df is not None and not df.empty:
                processed_df = bereik_utils.process_raw_bereik_data(df, target_group)
                db_utils.dump_to_sql(processed_df, 'tv.bereik')

        except Exception as e:
            logger.error(f"Error fetching bereik for flight {row.name}: {str(e)}")

def execute_query_to_df(query_key, params=None):
    if query_key not in query_dict:
        raise ValueError(f"Query key '{query_key}' not found in query_dict.")

    query = query_dict[query_key]

    if params:
        for key, value in params.items():
            query = query.replace(f':{key}', str(value))

    try:
        df = db_utils.query_to_df(query)
        if df is not None and not df.empty:
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")

def retrieve_and_format_flights(query_key):
    df = db_utils.query_to_df(query_dict[query_key])
    df['start_date'] = pd.to_datetime(df['start_date']).dt.strftime("%d%m%y")
    df['end_date'] = pd.to_datetime(df['end_date']).dt.strftime("%d%m%y")
    return df

def process_missing_flights(target_groups, df_flights, mock_campaign):
    for tg in target_groups:
        params = {'target_group': f"('{tg}')", 'mock_campaign': mock_campaign}
        df_missing_tg = execute_query_to_df('get_missing_flights', params)

        if df_missing_tg is not None and not df_missing_tg.empty:
            logger.info(f"{len(df_missing_tg)} missing flights for target group {tg} with COLLECT_MOCKS = {mock_campaign}:")
            filtered_flights_tg = df_flights[df_flights['flight_id'].isin(df_missing_tg['flight_id'])]
            get_bereik(filtered_flights_tg, tg)
        else:
            logger.info(f"No missing flights found for target group {tg} with COLLECT_MOCKS = {mock_campaign}.")

def update_running_flights(target_groups, df_flights):
    for tg in target_groups:
        params = {'target_group': f"('{tg}')"}
        df_duration_mismatch = execute_query_to_df('get_flights_with_duration_mismatch', params=params)

        if df_duration_mismatch is not None and not df_duration_mismatch.empty:
            logger.info(f"{len(df_duration_mismatch)} need an update")
            list_of_flights = df_duration_mismatch['flight_id'].unique().tolist()
            db_utils.delete_flights(list_of_flights, '[tv.bereik]', tg)

            filtered_flights_tg = df_flights[df_flights['flight_id'].isin(df_duration_mismatch['flight_id'])]
            get_bereik(filtered_flights_tg, tg)

if __name__ == "__main__":
    COLLECT_MOCKS = True
    STER_FLIGHTS_ONLY = True

    # Step 1: Retrieve flights data and format dates
    df_flights = retrieve_and_format_flights('get_flights')

    if STER_FLIGHTS_ONLY:
        df_flights = df_flights[df_flights['ster_grp'] > 0]

    # Step 2: Parse command line arguments
    args = parse_arguments()
    target_groups = args.tg if args.tg else mydict.target_groups

    # Step 3: Retrieve missing flights for each target group and process
    process_missing_flights(target_groups, df_flights, mock_campaign=0)

    # Step 4: Retrieve flights with duration mismatch that need to be updated
    update_running_flights(target_groups, df_flights)

    # Step 5: Collect mock flights
    if COLLECT_MOCKS:
        df_flights_mock = retrieve_and_format_flights('collect_mock_flights')

        if STER_FLIGHTS_ONLY:
            df_flights_mock = df_flights_mock[df_flights_mock['ster_grp'] > 0]

        process_missing_flights(target_groups, df_flights_mock, mock_campaign=1)
