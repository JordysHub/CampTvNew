# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.date_utils as date_utils
import camp_tv_new.src.utils.flights_utils as fu

import os
import pandas as pd

logger = setup_logger()

def read_processed_spots(processed_spots_folder, missing_dates):
    dfs = []
    for datum in missing_dates:
        processed_file_path = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
        df = pd.read_excel(processed_file_path)[['advertiser', 'product', 'date', 'hour', 'npo_1_grp', 'npo_2_grp', 'npo_3_grp', 'ster_grp', 'adalliance_grp', 'talpa_grp', 'total_grp']]
        dfs.append(df)
    return pd.concat(dfs)

def clean_hour_column(df):
    df['hour'] = df['hour'].str.replace('24:00:00', '00:00:00').str.replace('25:00:00', '01:00:00')
    df['hour'] = pd.to_datetime(df['hour'], format='%H:%M:%S')
    return df

def count_spots_and_grp(df):
    grouped_df = df.groupby(['advertiser', 'product', 'date']).agg(
        spot_count=('advertiser', 'size'),
        npo_1_grp=('npo_1_grp', 'sum'),
        npo_2_grp=('npo_2_grp', 'sum'),
        npo_3_grp=('npo_3_grp', 'sum'),
        ster_grp=('ster_grp', 'sum'),
        adalliance_grp=('adalliance_grp', 'sum'),
        talpa_grp=('talpa_grp', 'sum'),
        total_grp=('total_grp', 'sum')).reset_index()

    return grouped_df.sort_values(by=['date', 'advertiser', 'product'])
@timer_func
def update_all_spots_file(all_spots_path, processed_spots_folder):
    all_spots_file_dates = date_utils.get_existing_dates_in_all_spots(all_spots_path)
    existing_processed_spots_dates = date_utils.get_existing_dates_in_folder(processed_spots_folder)

    # Determine missing dates
    if all_spots_file_dates:
        missing_dates = [date for date in existing_processed_spots_dates if date not in all_spots_file_dates and date.month != 8]
    else:
        missing_dates = existing_processed_spots_dates

    if missing_dates:
        logger.info(f'Processing spots for all_spots file, from {min(missing_dates).strftime("%d-%m-%y")} to {max(missing_dates).strftime("%d-%m-%y")}')

        # Read processed spots into a DataFrame
        df_spots = read_processed_spots(processed_spots_folder, missing_dates)

        # Clean the 'hour' column
        df_spots = clean_hour_column(df_spots)

        # Count spots per day for each advertiser
        df_spots = count_spots_and_grp(df_spots)

        # create unqiue ID for every row
        df_spots['id'] = df_spots.apply(fu.generate_uuid_from_columns, data_type = 'spot', axis=1)

        # Append or write to all_spots_path
        try:
            all_spots_df = pd.read_excel(all_spots_path, parse_dates=["date"])
            all_spots_df = pd.concat([all_spots_df, df_spots])
            all_spots_df.sort_values(by=['date', 'advertiser', 'product'], inplace=True)
            all_spots_df.to_excel(all_spots_path, index=False)
        except FileNotFoundError:
            df_spots.sort_values(by=['date', 'advertiser', 'product'], inplace=True)
            df_spots.to_excel(all_spots_path, index=False)

    else:
        logger.debug('All spots are up to date')

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Define folder paths
    processed_spots_folder = os.getenv('processed_spots_folder')
    all_spots_path = os.getenv('all_spots_path')

    # Update all spots
    update_all_spots_file(all_spots_path, processed_spots_folder)
