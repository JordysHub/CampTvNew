# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.database_utils as db_utils

logger = setup_logger()

def preprocess_flights(df_spots: pd.DataFrame):
    segmented_df = fu.flights_segment_campaigns_by_new_start(df_spots)
    # grp_sum = segmented_df.groupby(['advertiser', 'product', 'flight_id'])[['npo1_grp', 'npo2_grp', 'npo3_grp', 'regio_grp', 'ster_grp', 'adalliance_grp', 'talpa_grp', 'total_grp']].sum().reset_index()
    grp_sum = segmented_df.groupby(['advertiser', 'product', 'flight_id'])[['npo1_grp', 'npo2_grp', 'npo3_grp', 'regio_grp', 'ster_grp']].sum().reset_index()
    dates_df = fu.get_start_end_campaign_date(segmented_df)
    df_flights = grp_sum.merge(dates_df, how='left', on=['advertiser', 'product', 'flight_id'])
    df_flights = fu.split_campaigns(df_flights, df_spots)
    return df_flights

def finalize_flights(df_flights: pd.DataFrame, data_type: str):
    df_flights['mock_campaign'] = (data_type == 'mock')
    df_flights['flight_id'] = df_flights.apply(fu.generate_uuid_from_columns, data_type=data_type, axis=1)
    df_flights.sort_values(['advertiser', 'product', 'start_date', 'end_date'], inplace=True)
    # df_flights = df_flights[['flight_id', 'advertiser', 'product', 'start_date', 'end_date', 'campaign_duration',
    #                          'npo1_grp', 'npo2_grp', 'npo3_grp',  'regio_grp', 'ster_grp',
    #                          'adalliance_grp', 'talpa_grp', 'total_grp', 'mock_campaign']]
    df_flights = df_flights[['flight_id', 'advertiser', 'product', 'start_date', 'end_date', 'campaign_duration',
                             'npo1_grp', 'npo2_grp', 'npo3_grp',  'regio_grp', 'ster_grp',
                             'mock_campaign']]

    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.date
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.date
    df_flights = df_flights[df_flights['campaign_duration'] > 5]
    df_flights = df_flights.fillna(0)

    return df_flights
@timer_func
def create_flights_from_spots(df_spots: pd.DataFrame):
    logger.debug("Creating flights from spots...")
    df_flights = preprocess_flights(df_spots)
    df_flights = finalize_flights(df_flights, data_type='flight')
    return df_flights

@timer_func
def create_mocks_from_flights(df_flights: pd.DataFrame, df_spots: pd.DataFrame):
    logger.debug("Creating mock campaigns from spots...")
    mock_campaigns_df = fu.create_mock_campaigns(df_flights, min_mock_duration=6)
    mock_campaigns_df = fu.calculate_grps_for_mock_campaigns(mock_campaigns_df, df_spots)
    mock_campaigns_df = finalize_flights(mock_campaigns_df, data_type='mock')
    return mock_campaigns_df


if __name__ == "__main__":
    CREATE_MOCKS = True
    table_name = "tv.flights_ster"

    # Read the entire table into a DataFrame
    df_spots = db_utils.query_to_df(f'SELECT * FROM [dbo].[tv.spots_ster]')
    existing_flights = db_utils.query_to_df(f'SELECT flight_id, campaign_duration FROM [dbo].[tv.flights_ster]')

    # Create flights from spots
    df_flights = create_flights_from_spots(df_spots)

    # Check if flights already exist in the database or that they need to be updated
    flights_to_delete_from_db = []
    for index, row in df_flights.iterrows():
        flight_id = row['flight_id']
        campaign_duration = row['campaign_duration']

        # Check if flight_id exists in the database
        if flight_id in existing_flights['flight_id'].values:
            existing_campaign_duration = existing_flights.loc[existing_flights['flight_id'] == flight_id, 'campaign_duration'].iloc[0]

            # Case 1: Campaign duration matches, delete from df_flights
            if campaign_duration == existing_campaign_duration:
                df_flights.drop(index, inplace=True)

            # Case 2: Campaign duration doesn't match, delete from database and dump new flight
            else:
                flights_to_delete_from_db.append(flight_id)

    # Calculate alcohol kansspelen
    logger.debug("Calculate alcohol/kansspelen...")
    df_flights = fu.kansspel_alcohol(df_flights)

    # Delete existing flights from the database that need an update
    logger.debug("Delete flights that need to be updated...")
    db_utils.delete_flights(flights_to_delete_from_db, table_name=table_name)
    db_utils.dump_to_sql(df_flights, table_name=table_name)

    # delete flights that can't be find in Edge (wrong advertiser/product combi)
    logger.debug("Delete flights that can't be find in Edge...")
    df_flights_to_delete = pd.read_excel('././warnings.xlsx')
    flights_to_delete = df_flights_to_delete['flight_id'].tolist()
    db_utils.delete_flights(flights_to_delete, table_name)

    if CREATE_MOCKS:
        # Create mocks from flights
        df_mocks = create_mocks_from_flights(df_flights, df_spots)
        # Check existing primary keys
        df_mocks_to_insert = db_utils.check_existing_primary_keys(df_mocks, table_name, 'flight_id')
        # Calculate alcohol kansspelen
        logger.debug("Calculate alcohol/kansspelen for mocks...")
        df_mocks_to_insert = fu.kansspel_alcohol(df_mocks_to_insert)

        if df_mocks_to_insert.shape[0] == 0:
            logger.info(f"No new rows to insert for {table_name}")
        else:
            logger.info(f"Number of rows to insert for {table_name}: {df_mocks_to_insert.shape[0]}")
            db_utils.dump_to_sql(df_mocks_to_insert, table_name=table_name)
