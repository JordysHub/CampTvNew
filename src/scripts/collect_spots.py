# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings

import argparse
import os
import time
from datetime import datetime, timedelta
import pandas as pd

from camp_tv_new.src.utils import api_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.date_utils as date_utils

# endregion

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
def get_spots(start_date: str, end_date: str, raw_spots_folder: str) -> pd.DataFrame:
    """
    Fetch spot data for the given date range and save to the specified folder.

    Parameters:
        start_date (str): The start date for fetching spots data in DDMMYY format.
        end_date (str): The end date for fetching spots data in DDMMYY format.
        raw_spots_folder (str): The folder to save raw spots data.

    Returns:
        pd.DataFrame: A DataFrame containing the fetched spots data.
    """
    existing_raw_spots_dates = date_utils.get_existing_dates_in_folder(raw_spots_folder)
    all_dates = date_utils.get_all_dates_in_range(start_date, end_date)
    missing_dates = [date for date in all_dates if date not in existing_raw_spots_dates and date.month != 8]

    if missing_dates:
        logger.info(f'Fetching spots from {min(missing_dates).strftime("%d-%m-%Y")} to {max(missing_dates).strftime("%d-%m-%Y")}')
        current_token_time = time.time()  # Get current time when starting
        token = api_utils.get_api_token()  # Fetch initial token

        for day in missing_dates:
            if time.time() - current_token_time >= 3000:
                logger.debug("Refreshing token...")
                token = api_utils.get_api_token()  # Fetch new token
                current_token_time = time.time()  # Update token refresh time

            day_str = day.strftime("%d%m%y")
            
            try:
                df = api_utils.call_kdh_getter_report(day_str, token)
            except Exception as e:
                logger.error(f"Failed to fetch data for {day_str}: {e}")
                continue
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            df.iloc[:, 5:] = df.iloc[:, 5:].astype(str)

            # Extract day, month, and year from the date string
            day_int, month_int, year_int = day_str[:2], day_str[2:4], '20' + day_str[4:6]
            directory = os.path.join(raw_spots_folder, year_int, month_int)
            
            # Create the directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)

            # Construct the file path and save the file
            file_path = os.path.join(directory, f"{day_int}.xlsx")
            df.to_excel(file_path, index=False)
            logger.debug(f"Fetched data for {day.strftime('%d-%m-%Y')} from Spots TV API")
                
    else:
        logger.debug('All daily spots have already been fetched')

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    raw_spots_folder = os.getenv("raw_spots_folder")
    args = parse_arguments()
    print(args.start_date, args.end_date, raw_spots_folder)
    get_spots(args.start_date, args.end_date, raw_spots_folder)
