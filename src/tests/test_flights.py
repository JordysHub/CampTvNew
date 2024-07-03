import pandas as pd
import pytest
import os
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import camp_tv_new.src.utils.database_utils as db_utils
import camp_tv_new.src.utils.connection_utils as con_utils

def query_to_df(query):
    engine = con_utils.create_sql_alchemy_engine()
    df_query = pd.read_sql_query(query, engine)

    return df_query

@pytest.fixture(scope='module')
def bereik_data():
    query = 'SELECT DISTINCT flight_id, target_group, campaign_duration FROM [dbo].[tv.bereik]'
    return query_to_df(query)

@pytest.fixture(scope='module')
def flights_data():
    query = 'SELECT flight_id, campaign_duration FROM [dbo].[tv.flights] WHERE mock_campaign = 0'
    return query_to_df(query)

@pytest.mark.parametrize('target_group', ['13+'])
def test_campaign_duration_for_target_group(target_group, bereik_data, flights_data):
    bereik_data_tg = bereik_data[bereik_data['target_group'] == target_group]
    flights_data_tg = flights_data.copy()

    # Dictionary to store mismatched durations
    mismatched_durations = {}

    for index, row in bereik_data_tg.iterrows():
        flight_id = row['flight_id']
        bereik_duration = row['campaign_duration']

        if flight_id in flights_data_tg['flight_id'].values:
            flights_duration = flights_data_tg.loc[flights_data_tg['flight_id'] == flight_id, 'campaign_duration'].iloc[0]

            if bereik_duration != flights_duration:
                mismatched_durations[flight_id] = (bereik_duration, flights_duration)

    assert not mismatched_durations, f"Mismatched campaign durations found for target group {target_group}: {mismatched_durations}"