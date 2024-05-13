# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import hashlib
import uuid
from datetime import datetime, timedelta

def flights_segment_campaigns_by_new_start(df: pd.DataFrame) -> pd.DataFrame:
    # preprocessing
    df = df[["advertiser", "product", "date"]].drop_duplicates()
    df = df.sort_values(by=["advertiser", "product", "date"]).reset_index(drop=True)

    # Calculate how many days between current date and last date
    df["difference_last"] = (abs(df["date"] - df["date"].shift(1)).apply(lambda x: x.days).fillna(0).astype(int))

    # New_start = start of a 'new' campaign, either because advertisers don't match or product doesn't match or more than 8 days between dates
    df["new_start"] = (df["difference_last"] > 8) | ((df["advertiser"] != df["advertiser"].shift(1)) | (df["product"] != df["product"].shift(1)))

    # create temp flight_id. Later unique ID will be created from advertiser, product and start_date 
    df['flight_id'] = np.where(df['new_start'], [str(uuid.uuid4()) for _ in range(len(df))], None)
    df['flight_id'] = df['flight_id'].fillna(method='ffill')  # future warning

    return df


def get_start_end_campaign_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function calculates the start_date and end_date for each flight.
    Output start_date and end_date in string DDMMYY format.
    """

    min_date_df = (df.groupby(["advertiser", "product", "flight_id"])["date"].min().to_frame().reset_index())
    min_date_df = min_date_df.rename(columns={"date": "start_date"})

    max_date_df = (df.groupby(["advertiser", "product", "flight_id"])["date"].max().to_frame().reset_index())
    max_date_df = max_date_df.rename(columns={"date": "end_date"})

    df = min_date_df.merge(max_date_df, how='left', on=['advertiser', 'product', 'flight_id'])
    df['campaign_duration'] = (df['end_date'] - df['start_date']).dt.days + 1
    df = df.loc[:, ['flight_id', 'advertiser', 'product', 'start_date', 'end_date', 'campaign_duration']]

    return df

def split_campaigns(df_flights):
    long_campaigns = df_flights[df_flights['campaign_duration'] > 60]
    new_campaigns = pd.DataFrame()
    for _, campaign in long_campaigns.iterrows():
        sub_campaigns = split_campaign(campaign)
        new_campaigns = pd.concat([new_campaigns, sub_campaigns], ignore_index=True)

    # Drop original rows from DataFrame and concatenate with split campaigns
    df_flights = df_flights.drop(long_campaigns.index)
    df_flights = pd.concat([df_flights, new_campaigns], ignore_index=True)
    df_flights = df_flights[df_flights['campaign_duration'] != 0]

    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.strftime("%d%m%y")
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.strftime("%d%m%y")
    df_flights.sort_values(by=['advertiser', 'product', 'start_date'], inplace=True)

    return df_flights

def split_campaign(campaign):
    campaign_duration = campaign['campaign_duration']
    start_date = campaign['start_date']
    end_date = campaign['end_date']

    sub_campaigns = []
    while campaign_duration > 60:
        next_start_date = (start_date + timedelta(days=61)).replace(day=1) 
        this_end_date = next_start_date - timedelta(days=1)
        this_campaign_duration = (this_end_date - start_date).days + 1

        campaign_data = {
            'flight_id': campaign['flight_id'],
            'advertiser': campaign['advertiser'],
            'product': campaign['product'],
            'start_date': start_date,
            'end_date': this_end_date,
            'campaign_duration': this_campaign_duration
        }
        sub_campaigns.append(campaign_data)

        # Update start date for next sub-campaign
        campaign_duration = (end_date - next_start_date).days + 1
        start_date = next_start_date

    # Add last sub-campaign
    campaign_data = {
        'flight_id': campaign['flight_id'],
        'advertiser': campaign['advertiser'],
        'product': campaign['product'],
        'start_date': start_date,
        'end_date': end_date,
        'campaign_duration': (end_date - start_date).days + 1
    }
    sub_campaigns.append(campaign_data)

    return pd.DataFrame(sub_campaigns)

# def combine_flights_df(df1, df2):

#     # Convert dates to datetime objects
#     df1['start_date'] = pd.to_datetime(df1['start_date'])
#     df1['end_date'] = pd.to_datetime(df1['end_date'])
#     df2['start_date'] = pd.to_datetime(df2['start_date'])
#     df2['end_date'] = pd.to_datetime(df2['end_date'])
#     # Merge dataframes based on advertiser and product
#     merged_df = pd.merge(df1, df2, on=['advertiser', 'product'], how='left', suffixes=('_first', '_second'))
#     # Calculate time difference between end_date of df1 and start_date of df2
#     merged_df['time_diff'] = merged_df['start_date_second'] - merged_df['end_date_first']
#     # Check if the time difference is within 8 days
#     merged_df['same_campaign'] = merged_df['time_diff'].apply(lambda x: abs(x.days) <= 8)
#     # Assign campaign_id from the first dataframe to the second dataframe
#     merged_df.loc[merged_df['same_campaign'], 'campaign_id_second'] = merged_df['campaign_id_first']
#     # Drop unnecessary columns
#     merged_df.drop(['start_date_first', 'end_date_first', 'start_date_second', 'end_date_second', 'time_diff'], axis=1, inplace=True)


def generate_uuid_from_columns(row):
    """
    Generates a (unique) UUID based on the values of the specified columns in the given row.
    Args:
        row (dict): A dictionary representing a row of data.
    Returns:
        uuid.UUID or None: The generated UUID or None if the UUID format is invalid.
    """
    # Concatenate values of the specified columns into a single string
    # Combination of advertiser, product, and start_date; no 'end-date' because the campaign can still run
    concatenated_string = ''.join(str(row[col]) for col in ['advertiser', 'product', 'start_date']).lower().replace(" ", "")

    # Hash the concatenated string using sha256
    hashed_value = hashlib.sha256(concatenated_string.encode()).digest()

    # Convert hash to UUID
    try:
        new_uuid = str(uuid.UUID(bytes=hashed_value[:16]))
        return new_uuid
    except ValueError:
        print("Invalid UUID format:", hashed_value)
        return None

def update_flights(df_flights_old, df_flights_new):

    # concat dataframes
    df_concat = pd.concat([df_flights_old, df_flights_new])
    # check which flights are updated with a new end_date/campaign_duration
    grouped = df_concat.groupby('flight_id').filter(lambda x: len(x) > 1 and len(x.drop_duplicates()) > 1)
    grouped = grouped.sort_values(by=['flight_id', 'campaign_duration'], ascending=[True, False]).groupby('flight_id').head(1)
    df_flights_updated = grouped.sort_values(by='flight_id')

    # check which flights are totally new
    new_flight_ids = set(df_flights_new['flight_id']) - set(df_flights_old['flight_id'])
    df_flights_new_unique = df_flights_new[df_flights_new['flight_id'].isin(new_flight_ids)]

    return df_flights_updated, df_flights_new_unique


"""
def process_flights_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    df["flight_id"] = df.apply(lambda x: create_unique_hash_id(x["advertiser"], x["product"], x["start_date"], x["end_date"]), axis=1)
    # Reshape so it can be send to SQL
    df = df.loc[:, ["flight_id", "advertiser", "product", "start_date", "end_date"]]

    # Change dates to string, 'cause SQL has trouble with datetime
    df["start_date"] = df["start_date"].dt.strftime("%d-%m-%Y")
    df["end_date"] = df["end_date"].dt.strftime("%d-%m-%Y")

    return df

"""