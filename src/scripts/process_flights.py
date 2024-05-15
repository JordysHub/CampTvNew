# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings
import camp_tv_new.src.utils.flights_utils as fu
from camp_tv_new.src.utils.logger import setup_logger, timer_func

from dotenv import load_dotenv
import pandas as pd
import warnings
import os

pd.set_option('future.no_silent_downcasting', True)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
# endregion

load_dotenv()
logger = setup_logger()


@timer_func
def create_flights_from_spots(df_spots: pd.DataFrame) -> pd.DataFrame:
    """
    """
    
    df_new_flights = fu.flights_segment_campaigns_by_new_start(df_spots)
    df_new_flights = fu.get_start_end_campaign_date(df_new_flights)
    # split flights that are longer than two months 
    df_new_flights = fu.split_campaigns(df_new_flights)
    # create unique flight_id
    df_new_flights['flight_id'] = df_new_flights.apply(fu.generate_uuid_from_columns, axis=1)
    df_new_flights.to_excel("./data/interim/flights/all_flights.xlsx", index=False)

    return df_new_flights

def main():
    df_spots = pd.read_excel("./data/interim/spots/all_spots.xlsx")
    create_flights_from_spots(df_spots)

if __name__ == "__main__":
    main()
