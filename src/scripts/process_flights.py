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
    df_new_flights = fu.split_campaigns(df_new_flights)
    df_new_flights['flight_id'] = df_new_flights.apply(fu.generate_uuid_from_columns, axis=1)

    try:
        # Update existing flights and identify new flights
        df_old_flights = pd.read_excel("./data/interim/flights/all_flights.xlsx", dtype={'start_date': str, 'end_date': str})
        df_updated_flights, df_new_unique_flights = fu.update_flights(df_old_flights, df_new_flights)

        # Write updated and new flights to Excel
        df_updated_flights.to_excel("./data/interim/flights/all_flights_updated.xlsx", index=False)
        df_new_unique_flights.to_excel("./data/interim/flights/all_flights_new.xlsx", index=False)

        # Overwrite old flights with new data
        df_old_flights.to_excel("./data/interim/flights/old/all_flights_old.xlsx", index=False)

    except:
        pass

    df_new_flights.to_excel("./data/interim/flights/all_flights.xlsx", index=False)

def main():
    # dtype_dict = {'start_date': str, 'end_date': str}
    # df_spots = pd.read_excel("./data/interim/spots/all_spots.xlsx", dtype=dtype_dict)
    df_spots = pd.read_excel("./data/interim/spots/all_spots.xlsx")

    create_flights_from_spots(df_spots)

if __name__ == "__main__":
    main()
