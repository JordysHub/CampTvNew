import pandas as pd
import pytest
import os


@pytest.fixture
def main_df_flights():
    # Create the main DataFrame with flight IDs
    main_df_flights = pd.read_excel('./data/external/all_flights.xlsx')
    return main_df_flights

@pytest.fixture
def target_groups_flights_raw():
    return load_dataframes('./data/raw/api/bereik')	

def load_dataframes(directory):
    dataframes = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.xlsx'):
                file_path = os.path.join(root, file)
                df = pd.read_excel(file_path, usecols=range(5))
                df = df.drop_duplicates()
                dataframes.append(df)
    return dataframes

##################################################################################################################################
def test_flight_ids():
    """
    Make sure all bereik df have the same amount of flights, and flight_ids are the same.
    """
    main_unique_ids = set(main_df_flights['flight_id'])

    for df in target_groups_flights_raw:
        df_unique_ids = set(df['flight_id'])
        if df_unique_ids != main_unique_ids:
            pytest.fail(f"{df} doesn't have the same flight_ids as main_df_flights")
            return False

    return True

def test_flights():
    """
    Make sure for all flights, the details are the same.
    """
    df_all_flights = main_df_flights

    for df in target_groups_flights_raw:

        for idx, row in df.iterrows():
            flight_id = row['flight_id']
            advertiser = row['advertiser']
            product = row['product']
            start_date = row['start_date']
            end_date = row['end_date']

            matching_row = df_all_flights[(df_all_flights['flight_id'] == flight_id) &
                                          (df_all_flights['advertiser'] == advertiser) &
                                          (df_all_flights['product'] == product) &
                                          (df_all_flights['start_date'] == start_date) &
                                          (df_all_flights['end_date'] == end_date)]

            assert not matching_row.empty, f"No matching row found in df_all_flights for flight ID {flight_id}"
