# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings

from camp_tv_new.src.utils import api_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func

import pandas as pd
from datetime import datetime, timedelta
import time
import argparse
import os

from dotenv import load_dotenv
# endregion

load_dotenv()
logger = setup_logger()

def parse_arguments(raw_spots_folder):
    """
    Parse command line arguments and return the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Get spots data.")
    parser.add_argument(
        "--start_date",
        type=api_utils.valid_date,
        default = (api_utils.get_last_known_date_offline(raw_spots_folder)[0].date() + timedelta(days=1)).strftime("%d%m%y"),
        help="Start date for data processing in the format DDMMYY (default: last date in database + 1 day)",
    )
    parser.add_argument(
        "--end_date",
        type=api_utils.valid_date,
        default=(datetime.now() - timedelta(days=6)).date().strftime("%d%m%y"),
        help="End date for data processing in the format DDMMYY (default: t-6)",
    )

    return parser.parse_args()

@timer_func
def get_spots(start_date: str, end_date: str, raw_spots_folder: str) -> pd.DataFrame:
    """
    """
    last_raw_spot_date = api_utils.get_last_known_date_offline(raw_spots_folder)[0].date()
    logger.info(f"Last raw spot data: {last_raw_spot_date}")
    logger.info(f"Retrieving Spots from start date: {start_date} to end date: {end_date}")
    start_date = datetime.strptime(start_date, "%d%m%y")
    end_date = datetime.strptime(end_date, "%d%m%y")

    assert start_date <= end_date, "ERROR - End date is before start date"

    date_range = pd.date_range(start_date, end_date)
    current_token_time = time.time()  # Get current time when starting
    token = api_utils.get_api_token()  # Fetch initial token

    for day in date_range:
        if time.time() - current_token_time >= 3000:
            logger.debug("Refreshing token...")
            token = api_utils.get_api_token()  # Fetch new token
            current_token_time = time.time()  # Update token refresh time

        day_str = day.strftime("%d%m%y")
        df = api_utils.call_kdh_getter_report(day_str, token)
        df['date'] = pd.to_datetime(df['date']).dt.date
        # convert lists to strings to prevent reading errors in pandas
        for col in df.columns[5:]:
            df[col] = df[col].apply(str)

        day_int = day_str[0:2]
        month_int = day_str[2:4]
        year_int = '20' + day_str[4:6]
        directory = f"{raw_spots_folder}{year_int}/{month_int}/"
        if not os.path.exists(directory):
            os.makedirs(directory)
        df.to_excel(f"{raw_spots_folder}{year_int}/{month_int}/{day_int}.xlsx", index=False)
        logger.debug("Fetched data for {} from Spots TV API".format(day.strftime("%d-%m-%Y")))

def main():
    """
    Main function to process data based on command line arguments.
    """
    raw_spots_folder = "data/raw/api/spots/"

    args = parse_arguments(raw_spots_folder)
    get_spots(args.start_date, args.end_date, raw_spots_folder)

if __name__ == "__main__":
    main()
