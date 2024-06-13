# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from utils.logger import setup_logger

logger = setup_logger()

def collect_raw_spots(raw_spots_folder, processed_spots_folder, missing_dates):
    if not missing_dates:
        logger.debug('Processed all daily spots')
        return
    
    logger.info(f'Processing spots from {min(missing_dates).strftime('%d-%m-%y')} to {max(missing_dates).strftime('%d-%m-%y')}')
    
    for datum in missing_dates:
        process_date(datum, raw_spots_folder, processed_spots_folder)

def process_date(datum, raw_spots_folder, processed_spots_folder):
    raw_file_path = os.path.join(raw_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
    processed_file_path = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
    processed_root_folder = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/'))

    os.makedirs(processed_root_folder, exist_ok=True)

    df = pd.read_excel(raw_file_path, parse_dates=['date'])
    df['date'] = pd.to_datetime(df['date']).dt.date

    # Convert strings in GRP columns to lists (as returned by the API)
    columns_to_apply_eval = df.columns[5:]
    df[columns_to_apply_eval] = df[columns_to_apply_eval].apply(lambda x: x.map(eval))

    df = prep_spots.tv_clean_df(df)
    df_ids = prep_spots.determine_ids(df)
    df = prep_spots.add_dayparts(df)

    df = df.merge(df_ids, on=["advertiser", "product"], how="left").sort_values(by=["date", "advertiser"])
    df.to_excel(processed_file_path, index=False)
    
if __name__ == "__main__":
    from dotenv import load_dotenv
    import camp_tv_new.src.utils.preprocess_spots as prep_spots
    import camp_tv_new.src.utils.date_utils as date_utils

    load_dotenv()

    raw_spots_folder = os.getenv("raw_spots_folder")
    processed_spots_folder = os.getenv("processed_spots_folder")
    
    existing_raw_spots_dates = date_utils.get_existing_dates_in_folder(raw_spots_folder)
    existing_processed_spots_dates = date_utils.get_existing_dates_in_folder(processed_spots_folder)
    missing_dates = [date for date in existing_raw_spots_dates if date not in existing_processed_spots_dates and date.month != 8] # skipping August because this data is incorrect
    
    collect_raw_spots(raw_spots_folder, processed_spots_folder, missing_dates)


