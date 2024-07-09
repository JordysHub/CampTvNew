
import camp_tv_new.src.utils.api_utils as api_utils
import pandas as pd
from tqdm import tqdm

def calculate_alcohol_kansspelen(df_flights: pd.DataFrame):

    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.strftime("%d%m%y")
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.strftime("%d%m%y")
    results = {}

    token = api_utils.get_api_token()
    for idx, row in tqdm(df_flights.iterrows(), total=len(df_flights), position=0, ncols=120,
                         bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}"):

        flight_id = row['flight_id']
        advertiser = row['advertiser']
        product = row['product']
        start_date = row['start_date']
        end_date = row['end_date']
        day = start_date + '-' + end_date

        spots_in_flight = api_utils.call_kdh_getter_report(advertiser = advertiser, product = product, token = token, day=day)
        spots_in_flight = spots_in_flight.iloc[:, 3]
        spots_in_flight = spots_in_flight.str.replace('24:00:00', '00:00:00').str.replace('25:00:00', '01:00:00')

        # Check if all hours are between 21 and 2
        spots_in_flight = pd.to_datetime(spots_in_flight, format='%H:%M:%S').dt.hour

        # Check if all hours are between 21 and 2
        is_night_time = spots_in_flight.between(21, 23) | spots_in_flight.between(0, 1)
        all_night_time = is_night_time.all()

        # Store result in dictionary
        results[flight_id] = all_night_time

    # Add the results to the DataFrame as a new column
    df_flights['alcohol_kansspelen'] = df_flights['flight_id'].map(results)

    return df_flights
