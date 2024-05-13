from datetime import datetime
import pandas as pd
import os
import camp_tv_new.src.utils.preprocess_spots as prep_spots

from dotenv import load_dotenv
from utils.logger import setup_logger
from camp_tv_new.src.utils import api_utils

load_dotenv()
logger = setup_logger()

def fetch_latest_date(folder_path):
    return api_utils.get_last_known_date_offline(folder_path)[0]

def process_raw_spots(raw_folder_path, processed_folder_path):
    latest_raw_date = fetch_latest_date(raw_folder_path)
    latest_processed_date = fetch_latest_date(processed_folder_path)

    if latest_processed_date < latest_raw_date:
        date_range = pd.date_range(start=latest_processed_date + pd.DateOffset(days=1), end=latest_raw_date)
        for datum in date_range:
            raw_file_path = os.path.join(raw_folder_path, datum.strftime('%Y/%m/%d') + '.xlsx')
            processed_file_path = os.path.join(processed_folder_path, datum.strftime('%Y/%m/%d') + '.xlsx')
            processed_root_folder = os.path.join(processed_folder_path, datum.strftime('%Y/%m/'))

            if not os.path.exists(processed_root_folder):
                os.makedirs(processed_root_folder)

            df = pd.read_excel(raw_file_path, parse_dates=['date'])
            df['date'] = pd.to_datetime(df['date']).dt.date

            # convert strings in GRP columns to lists (as returned by the API)
            for col in df.columns[5:]:
                df[col] = df[col].apply(eval)

            df = prep_spots.tv_clean_df(df)
            df_ids = prep_spots.determine_ids(df)
            df = prep_spots.add_dayparts(df)

            df = df.merge(df_ids, on=["advertiser", "product"], how="left").sort_values(by=["date", "advertiser"])
            df.to_excel(processed_file_path, index=False)
    else:
        logger.debug('Processed all daily spots')

def update_all_spots(all_spots_path, processed_folder_path):
    try:
        all_spots_df = pd.read_excel(all_spots_path, parse_dates=["date"])
        latest_spots_date = all_spots_df['date'].max()
    except FileNotFoundError:
        latest_spots_date = datetime(2023, 8, 31)
    dfs = []

    latest_processed_date = fetch_latest_date(processed_folder_path)
    if latest_spots_date < latest_processed_date:
        date_range = pd.date_range(start=latest_spots_date + pd.DateOffset(days=1), end=latest_processed_date)
        logger.debug(f'Processing spots from {min(date_range).date()} to {max(date_range).date()}')
        for datum in date_range:
            processed_file_path = os.path.join(processed_folder_path, datum.strftime('%Y/%m/%d') + '.xlsx')
            df = pd.read_excel(processed_file_path)[["advertiser", "product", "date"]].drop_duplicates()
            dfs.append(df)

        df_spots = pd.concat(dfs)
        df_spots['date'] = pd.to_datetime(df_spots['date']).dt.date
        try:
            all_spots_df = pd.concat([all_spots_df, df_spots])
            all_spots_df.to_excel(all_spots_path, index=False)
        except UnboundLocalError: 
            df_spots.to_excel(all_spots_path, index=False)
    else: 
        logger.debug('Fetched and concatenated all spots')

def main():

    # Define folder paths
    raw_spots_folder = "./data/raw/api/spots/"
    processed_spots_folder = "./data/processed/spots/"
    all_spots_path = "./data/interim/spots/all_spots.xlsx"

    # Process raw spots
    process_raw_spots(raw_spots_folder, processed_spots_folder)
    last_raw_spot_data = api_utils.get_last_known_date_offline(raw_spots_folder)[0].date()
    logger.info(f"Processed new fetched spots. Last raw spot data: {last_raw_spot_data}")
    # Update all spots
    update_all_spots(all_spots_path, processed_spots_folder)
    df = pd.read_excel(all_spots_path)
    logger.info(f"Updated all_spots file. First and last date in spots file: {df['date'].min().date()} - {df['date'].max().date()}")

if __name__ == "__main__":
    main()