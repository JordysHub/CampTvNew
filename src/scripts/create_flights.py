# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.query_dict import Queries

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
    mock_campaigns_df = fu.create_mock_campaigns(df_flights, min_mock_duration=6, max_allowed_overlap = 0.8, max_attempts=30)
    mock_campaigns_df = fu.calculate_grps_for_mock_campaigns(mock_campaigns_df, df_spots)
    mock_campaigns_df = finalize_flights(mock_campaigns_df, data_type='mock')
    return mock_campaigns_df

if __name__ == "__main__":
    CREATE_MOCKS = False
    table_name = "tv.flights_ster"

    # Read the entire table into a DataFrame
    df_spots = db_utils.query_to_df('SELECT * FROM [dbo].[tv.spots_ster]')

    # # Create flights from spots
    df_flights = create_flights_from_spots(df_spots)
    logger.debug(f"Calculate alcohol/kansspelen...{len(df_flights)} flights to calculate")
    df_flights = fu.kansspel_alcohol(df_flights)

    # Fetch and delete all normal flights (not the mock campaigns), in order to update them
    # Mock campaigns can be kept, because these will not change anymore
    df_flights_to_delete = db_utils.query_to_df('SELECT flight_id FROM [dbo].[tv.flights_ster] where mock_campaign = 0')
    df_flights_to_delete = df_flights_to_delete['flight_id'].to_list()
    if len(df_flights_to_delete) > 0:
        db_utils.delete_flights(df_flights_to_delete['flight_id'].to_list(), table_name=table_name)

    # Dump new flights to SQL database
    db_utils.dump_to_sql(df_flights, table_name=table_name, if_exists='append')

    # Delete the flights from the bereik table, where the campaign duration doesn't match anymore; these flights are updated and bereik need to be fetched again
    flights_to_delete = db_utils.query_to_df(Queries.delete_bereik_flights_which_dont_match())
    if len(flights_to_delete) > 0:
        db_utils.delete_flights(flights_to_delete['flight_id'].to_list(), table_name='tv.bereik_ster')

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
