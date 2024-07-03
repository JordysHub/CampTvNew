# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from camp_tv_new.src.utils import api_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.process_spots as proc_spots
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.database_utils as db_utils

import argparse
import os
import time
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

logger = setup_logger()

def parse_arguments():
    """
    Parse command line arguments and return the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Get spots data.")
    parser.add_argument(
        "--start_date",
        type=api_utils.valid_date,
        default = os.getenv("collecting_start_date"),
        help="...",
    )
    parser.add_argument(
        "--end_date",
        type=api_utils.valid_date,
        default=(datetime.now() - timedelta(days=6)).date().strftime("%d%m%y"),
        help="End date for data processing in the format DDMMYY (default: t-6)",
    )

    return parser.parse_args()

def get_missing_dates(start_date: str, end_date: str, existing_dates: list) -> list:
    """
    Get the missing dates that are not in the existing_dates list.

    Parameters:
        start_date (str): The start date for the date range in DDMMYY format.
        end_date (str): The end date for the date range in DDMMYY format.
        existing_dates (list): List of existing dates.

    Returns:
        list: List of missing dates.
    """
    start_date = pd.to_datetime(start_date, format='%d%m%y')
    end_date = pd.to_datetime(end_date, format='%d%m%y')
    all_dates = pd.date_range(start=start_date, end=end_date)
    missing_dates = [date for date in all_dates if date not in existing_dates and date.month != 8]
    return missing_dates

def fetch_spots_for_date(day_str: str, token: str) -> pd.DataFrame:
    """
    Fetch spots data for a specific date.

    Parameters:
        day_str (str): The date string in DDMMYY format.
        token (str): The API token.

    Returns:
        pd.DataFrame: DataFrame containing the spots data.
    """
    try:
        df = api_utils.call_kdh_getter_report(day_str, token)
        df = proc_spots.process_spots_day(df, pd.to_datetime(day_str, format="%d%m%y"))
        return df
    except Exception as e:
        logger.error(f"Failed to fetch data for {day_str}: {e}")
        return pd.DataFrame()

@timer_func
def get_spots(start_date: str, end_date: str, existing_dates: list) -> pd.DataFrame:
    """
    Fetch spot data for the given date range and save to the specified folder.

    Parameters:
        start_date (str): The start date for fetching spots data in DDMMYY format.
        end_date (str): The end date for fetching spots data in DDMMYY format.
        existing_dates (list): List of existing dates.

    Returns:
        pd.DataFrame: A DataFrame containing the fetched spots data.
    """
    df_spots = pd.DataFrame()
    missing_dates = get_missing_dates(start_date, end_date, existing_dates)

    if missing_dates:
        logger.info(f'Fetching spots from {min(missing_dates).strftime("%d-%m-%Y")} to {max(missing_dates).strftime("%d-%m-%Y")}')
        current_token_time = time.time()
        token = api_utils.get_api_token()

        for day in tqdm(missing_dates, desc="Fetching spots data"):

            if time.time() - current_token_time >= 3000:
                token = api_utils.get_api_token()
                current_token_time = time.time()

            day_str = day.strftime("%d%m%y")
            df = fetch_spots_for_date(day_str, token)
            df_spots = pd.concat([df_spots, df], ignore_index=True)

        df_spots = proc_spots.clean_hour_column(df_spots)
        df_spots = proc_spots.count_spots_and_grp(df_spots)
        df_spots['ID'] = df_spots.apply(fu.generate_uuid_from_columns, data_type='spots', axis=1)
        df_spots.insert(0, 'ID', df_spots.pop('ID'))

    else:
        logger.debug('All daily spots have already been collected')

    return df_spots

if __name__ == "__main__":

    table_name = "tv.spots"
    args = parse_arguments()
    existing_dates = db_utils.get_all_dates_from_db()

    df_spots = get_spots(args.start_date, args.end_date, existing_dates)
    df_to_insert =  db_utils.check_existing_primary_keys(df_spots, 'tv.spots', 'ID')

    if df_to_insert.shape[0] == 0:
        logger.info(f"No new rows to insert for {table_name}")
    else:
        logger.info(f"Number of rows to insert for {table_name}: {df_to_insert.shape[0]}")
        db_utils.dump_to_sql(df_to_insert, table_name = table_name)
