# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from camp_tv_new.src.utils import api_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.process_spots as proc_spots
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.query_dict import query_dict

import argparse
import os
import time
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Setup logger
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

@timer_func
def get_spots(missing_dates: list) -> pd.DataFrame:
    df_spots = pd.DataFrame()

    if missing_dates:
        logger.info(f'Fetching spots from {min(missing_dates).strftime("%d-%m-%Y")} to {max(missing_dates).strftime("%d-%m-%Y")}')
        current_token_time = time.time()
        token = api_utils.get_api_token()

        for day in tqdm(missing_dates, total=len(missing_dates), position=0, ncols=120,
                         desc=f"Fetching spots data",
                         bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):

            if time.time() - current_token_time >= 3000:
                token = api_utils.get_api_token()
                current_token_time = time.time()

            day_str = day.strftime("%d%m%y")
            df = fetch_spots_for_date(day_str, token)
            df_spots = pd.concat([df_spots, df], ignore_index=True)

        df_spots = proc_spots.clean_hour_column(df_spots)

        # Save DataFrame to Excel before further processing
        save_to_excel(df_spots)

        df_spots = proc_spots.count_spots_and_grp(df_spots)
        df_spots['ID'] = df_spots.apply(fu.generate_uuid_from_columns, data_type='spots', axis=1)
        df_spots.insert(0, 'ID', df_spots.pop('ID'))

    else:
        logger.debug('All daily spots have already been collected')

    return df_spots

def save_to_excel(df: pd.DataFrame):
    try:
        df['date'] = pd.to_datetime(df['date']).dt.date
        df_all_spots = pd.read_excel("../data/interim/all_spots_ster.xlsx", engine='openpyxl')
        df_all_spots = pd.concat([df_all_spots, df], ignore_index=True)
        df.sort_values(by=['advertiser', 'product', 'date', 'hour'], ignore_index=True, inplace=True)
        df.drop_duplicates(subset=['advertiser', 'product', 'date', 'hour'], keep='last', ignore_index=True, inplace=True)
        df.to_excel("././data/interim/all_spots_ster.xlsx", index=False)
    except FileNotFoundError:
        pass

    except Exception as e:
        logger.error(f"Failed to save to Excel: {e}")

def fetch_spots_for_date(day_str: str, token: str) -> pd.DataFrame:
    try:
        df = api_utils.call_kdh_getter_report(day_str, token)
        df = proc_spots.process_spots_day(df, pd.to_datetime(day_str, format="%d%m%y"))
        return df
    except Exception as e:
        logger.error(f"Failed to fetch data for {day_str}: {e}")
        return pd.DataFrame()

def get_missing_dates(start_date, end_date) -> list:
    """
    Get the missing dates from the spots db.

    Parameters:
        start_date (str): The start date for the date range in DDMMYY format.
        end_date (str): The end date for the date range in DDMMYY format.
        existing_dates (list): List of existing dates.

    Returns:
        list: List of missing dates.
    """
    start_date = pd.to_datetime(start_date, format='%d%m%y')
    end_date = pd.to_datetime(end_date, format='%d%m%y')

    # Get existing dates in db
    existing_dates_df = db_utils.query_to_df(query_dict['get_existing_dates_from_spots'])

    # Filter existing dates for all months except August 2023
    existing_dates_df['date'] = pd.to_datetime(existing_dates_df['date'], format='%d%m%y')
    existing_dates_df = existing_dates_df[
        ~((existing_dates_df['date'].dt.year == 2023) & (existing_dates_df['date'].dt.month == 8))
    ]
    list_of_existing_dates = existing_dates_df['date'].tolist()

    # Generate all dates in the range from start_date to end_date
    all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    # Find missing dates that are not in list_of_existing_dates and not in August 2023
    missing_dates = [
        date for date in all_dates
        if (date not in list_of_existing_dates) and not (date.year == 2023 and date.month == 8)
    ]

    return missing_dates

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    table_name = 'tv.spots_ster'
    args = parse_arguments()

    missing_dates = get_missing_dates(args.start_date, args.end_date)
    df_spots = get_spots(missing_dates)

    if not df_spots.empty:
        df_to_insert = db_utils.check_existing_primary_keys(df_spots, table_name, 'ID')

        if not df_to_insert.empty:
            logger.info(f"Number of rows to insert for {table_name}: {df_to_insert.shape[0]}")
            db_utils.dump_to_sql(df_to_insert, table_name=table_name)
        else:
            logger.info(f"No new rows to insert for {table_name}")
    else:
        logger.info(f"No new rows to insert for {table_name}")
