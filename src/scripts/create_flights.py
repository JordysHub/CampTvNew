# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.dictionaries as mydict


logger = setup_logger()

@timer_func
def create_flights_from_spots(df_spots: pd.DataFrame, all_flights_path: str):
    
    df_flights = fu.flights_segment_campaigns_by_new_start(df_spots)
    df_flights = fu.get_start_end_campaign_date(df_flights)
    df_flights = fu.split_campaigns(df_flights)
    
    # create mock campaigns
    df_flights['mock_campaign'] = False
    mock_campaigns_df = fu.create_mock_campaigns(df_flights)

    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.strftime("%d%m%y")
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.strftime("%d%m%y")
    mock_campaigns_df['start_date'] = pd.to_datetime(mock_campaigns_df['start_date']).dt.strftime("%d%m%y")
    mock_campaigns_df['end_date'] = pd.to_datetime(mock_campaigns_df['end_date']).dt.strftime("%d%m%y")
    
    df_flights['flight_id'] = df_flights.apply(fu.generate_uuid_from_columns, axis=1)
    mock_campaigns_df['flight_id'] = mock_campaigns_df.apply(fu.generate_uuid_from_columns, axis=1)
    
    # delete flights from file which give errors in edge or have changed over time
    rows_to_delete_indices = df_flights[df_flights['flight_id'].isin(mydict.wrong_campaigns)].index
    rows_to_delete = df_flights.iloc[rows_to_delete_indices]
    logger.info(f"These rows will be deleted: \n {rows_to_delete}")
    ids_to_delete = rows_to_delete['flight_id'].tolist()
    df_flights = df_flights[~df_flights['flight_id'].isin(ids_to_delete)]
    
    df_flights.sort_values(['advertiser', 'product', 'start_date', 'end_date'], inplace=True)
    mock_campaigns_df.sort_values(['advertiser', 'product', 'start_date', 'end_date'], inplace=True)
    df_flights.to_excel(all_flights_path, index=False)
    mock_campaigns_df.to_excel(all_flights_path.replace(".xlsx", "_mock.xlsx"), index=False)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    all_spots_path = os.getenv("all_spots_path")
    all_flights_path = os.getenv("all_flights_path")

    df_spots = pd.read_excel(all_spots_path)
    create_flights_from_spots(df_spots, all_flights_path)
