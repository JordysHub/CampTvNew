# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import math
import hashlib
import uuid
from datetime import timedelta
from tqdm import tqdm
import logging

import src.utils.database_utils as db_utils

logger = logging.getLogger("MyLogger")


def flights_segment_campaigns_by_new_start(df: pd.DataFrame) -> pd.DataFrame:
    df = df[
        [
            "advertiser",
            "product",
            "date",
            "npo1_grp",
            "npo2_grp",
            "npo3_grp",
            "regio_grp",
            "ster_grp",
            "alcohol_kansspelen"
        ]
    ].drop_duplicates()

    df = df.sort_values(by=["advertiser", "product", "date"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])

    # Calculate how many days between current date and last date
    df["difference_last"] = (
        abs(df["date"] - df["date"].shift(1))
        .apply(lambda x: x.days)
        .fillna(0)
        .astype(int)
    )

    # New_start = start of a 'new' campaign, either because advertisers don't match or product doesn't match or more than 8 days between dates
    df["new_start"] = (df["difference_last"] > 8) | (
        (df["advertiser"] != df["advertiser"].shift(1))
        | (df["product"] != df["product"].shift(1))
    )

    # create temp flight_id. Later unique ID will be created from advertiser, product and start_date
    df["flight_id"] = np.where(
        df["new_start"], [str(uuid.uuid4()) for _ in range(len(df))], None
    )

    df["flight_id"] = df["flight_id"].ffill()  # future warning

    return df


def get_start_end_campaign_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function calculates the start_date and end_date for each flight.
    Output start_date and end_date in string DDMMYY format.
    """
    min_date_df = (
        df.groupby(["advertiser", "product", "flight_id"])["date"]
        .min()
        .to_frame()
        .reset_index()
    )
    min_date_df = min_date_df.rename(columns={"date": "start_date"})

    max_date_df = (
        df.groupby(["advertiser", "product", "flight_id"])["date"]
        .max()
        .to_frame()
        .reset_index()
    )
    max_date_df = max_date_df.rename(columns={"date": "end_date"})

    df = min_date_df.merge(
        max_date_df, how="left", on=["advertiser", "product", "flight_id"]
    )
    df["campaign_duration"] = (df["end_date"] - df["start_date"]).dt.days + 1
    df = df.loc[
        :,
        [
            "flight_id",
            "advertiser",
            "product",
            "start_date",
            "end_date",
            "campaign_duration"
        ],
    ]

    return df


def split_campaigns(df_flights, df_spots):
    long_campaigns = df_flights[df_flights["campaign_duration"] > 60]
    new_campaigns = pd.DataFrame()
    for _, campaign in long_campaigns.iterrows():
        sub_campaigns = split_campaign(campaign)
        new_campaigns = pd.concat([new_campaigns, sub_campaigns], ignore_index=True)

    # re-calculate grps for splitted campaigns
    new_campaigns["start_date"] = pd.to_datetime(new_campaigns["start_date"])
    new_campaigns["end_date"] = pd.to_datetime(new_campaigns["end_date"])
    df_spots["date"] = pd.to_datetime(df_spots["date"])

    # Sum GRPs for the new campaigns
    df_new_campaigns = sum_grps_for_splitted_campaigns(new_campaigns, df_spots)

    # Drop original rows from DataFrame and concatenate with split campaigns
    df_flights = df_flights.drop(long_campaigns.index)
    df_flights = pd.concat([df_flights, df_new_campaigns], ignore_index=True)
    df_flights = df_flights[df_flights["campaign_duration"] != 0]

    return df_flights


def split_campaign(campaign):
    campaign_duration = campaign["campaign_duration"]
    start_date = campaign["start_date"]
    end_date = campaign["end_date"]

    sub_campaigns = []
    while campaign_duration > 60:
        next_start_date = (start_date + timedelta(days=61)).replace(day=1)
        this_end_date = next_start_date - timedelta(days=1)
        this_campaign_duration = (this_end_date - start_date).days + 1

        campaign_data = {
            "flight_id": campaign["flight_id"],
            "advertiser": campaign["advertiser"],
            "product": campaign["product"],
            "start_date": start_date,
            "end_date": this_end_date,
            "campaign_duration": this_campaign_duration,
            "alcohol_kansspelen": campaign["alcohol_kansspelen"],
        }
        sub_campaigns.append(campaign_data)

        # Update start date for next sub-campaign
        campaign_duration = (end_date - next_start_date).days + 1
        start_date = next_start_date

    # Add last sub-campaign
    campaign_data = {
        "flight_id": campaign["flight_id"],
        "advertiser": campaign["advertiser"],
        "product": campaign["product"],
        "start_date": start_date,
        "end_date": end_date,
        "campaign_duration": (end_date - start_date).days + 1,
        "alcohol_kansspelen": campaign["alcohol_kansspelen"]
    }
    sub_campaigns.append(campaign_data)

    return pd.DataFrame(sub_campaigns)


def sum_grps_for_splitted_campaigns(df_new_campaigns, df_spots):
    # Initialize GRP columns with 0
    grp_cols = ["npo1_grp", "npo2_grp", "npo3_grp", "regio_grp", "ster_grp"]
    for col in grp_cols:
        df_new_campaigns[col] = 0.0

    # Iterate over each new campaign row
    for index, row in df_new_campaigns.iterrows():
        # Filter df_spots based on advertiser, product, and date range
        mask = (
            (df_spots["advertiser"] == row["advertiser"])
            & (df_spots["product"] == row["product"])
            & (df_spots["date"] >= row["start_date"])
            & (df_spots["date"] <= row["end_date"])
        )
        filtered_spots = df_spots[mask]

        # Sum the GRP columns for the filtered rows
        summed_grps = filtered_spots[grp_cols].sum()

        # Assign the summed GRPs to the respective columns in df_new_campaigns
        for col in grp_cols:
            df_new_campaigns.at[index, col] = summed_grps[col]

    return df_new_campaigns


def generate_uuid_from_columns(row, data_type):
    """
    Generates a (unique) UUID based on the values of the specified columns in the given row.
    Args:
        row (dict): A dictionary representing a row of data.
    Returns:
        uuid.UUID or None: The generated UUID or None if the UUID format is invalid.
    """

    def format_date(value):
        if pd.isnull(value):
            return ""
        return pd.to_datetime(value).strftime("%d%m%y")

    # Concatenate values of the specified columns into a single string
    # Combination of advertiser, product, and start_date; no 'end-date' because the campaign can still run at this moment

    if data_type == "mock":
        concatenated_string = (
            "".join(
                (
                    str(row[col])
                    if col not in ["start_date", "end_date"]
                    else format_date(row[col])
                )
                for col in ["advertiser", "product", "start_date", "end_date"]
            )
            .lower()
            .replace(" ", "")
        )
    elif data_type == "flight":
        concatenated_string = (
            "".join(
                str(row[col]) if col != "start_date" else format_date(row[col])
                for col in ["advertiser", "product", "start_date"]
            )
            .lower()
            .replace(" ", "")
        )
    elif data_type == "spots":
        concatenated_string = (
            "".join(
                str(row[col]) if col != "date" else format_date(row[col])
                for col in ["advertiser", "product", "date"]
            )
            .lower()
            .replace(" ", "")
        )

    # Hash the concatenated string using sha256
    hashed_value = hashlib.sha256(concatenated_string.encode()).digest()

    # Convert hash to UUID
    try:
        new_uuid = str(uuid.UUID(bytes=hashed_value[:16]))
        return new_uuid
    except ValueError:
        print("Invalid UUID format:", hashed_value)
        return None


def check_alcohol_kansspelen(df_flights):
    query_spots = """
        SELECT *
        FROM [dbo].[tv.spots_ster]
        order by date, advertiser;
        """
    all_spots = db_utils.query_to_df(query_spots)

    # Initialize alcohol_kansspelen column to 0
    df_flights['alcohol_kansspelen'] = 0

    def update_alcohol_label(flights, spots):
        for index, flight in flights.iterrows():
            # Filter spots for the current flight's advertiser, product, and date range
            flight_spots = spots[
                (spots['advertiser'] == flight['advertiser'])
                & (spots['product'] == flight['product'])
                & (spots['date'] >= flight['start_date'])
                & (spots['date'] <= flight['end_date'])
            ]

            # Check if all rows for alcohol_kansspelen are True (1)
            if len(flight_spots) > 0 and flight_spots['alcohol_kansspelen'].all():
                flights.at[index, 'alcohol_kansspelen'] = 1  # Mark as True/1
            else:
                flights.at[index, 'alcohol_kansspelen'] = 0  # Mark as False/0

    update_alcohol_label(df_flights, all_spots)

    return df_flights

############ MOCK FLIGHTS ################


def create_mock_campaigns(
    df_flights,
    min_days_gap=5,
    max_mock_duration_ratio=0.8,
    max_allowed_overlap=0.8,
    max_mock_campaigns=10,
    max_attempts=50,
    min_mock_duration=5,
):
    """
    Generates mock campaigns based on the provided flights data.

    Parameters:
    df_flights (pd.DataFrame): The DataFrame containing the flights data.
    min_days_gap (int, optional): The minimum gap in days between the start date of the mock campaign and the start date of the original campaign. Defaults to 4.
    max_mock_duration_ratio (float, optional): The maximum ratio of the mock campaign duration to the original campaign duration. Defaults to 0.9.
    max_allowed_overlap (float, optional): The maximum allowed overlap between the mock campaign and other mock campaigns. Defaults to 0.8.
    max_mock_campaigns (int, optional): The maximum number of mock campaigns to generate. Defaults to 10.
    max_attempts (int, optional): The maximum number of attempts to generate a mock campaign. Defaults to 50.
    min_mock_duration (int, optional): The minimum duration of the mock campaign. Defaults to 1.

    Returns:
    pd.DataFrame: A DataFrame containing the generated mock campaigns.
    """
    new_mock_campaigns = []
    df_flights["start_date"] = pd.to_datetime(df_flights["start_date"], format="%d%m%y")
    df_flights["end_date"] = pd.to_datetime(df_flights["end_date"], format="%d%m%y")

    for _, row in tqdm(
        df_flights.iterrows(), total=len(df_flights), desc="Generating Mock Campaigns"
    ):
        original_duration = row["campaign_duration"]
        max_mock_duration = max(
            min_mock_duration, math.floor(original_duration * max_mock_duration_ratio)
        )

        if min_days_gap > max_mock_duration:
            continue

        num_mock_campaigns = 0
        attempts = 0
        current_campaign_mocks = []
        too_much_overlap = False

        while num_mock_campaigns < max_mock_campaigns and attempts < max_attempts:
            if original_duration > 30:
                mock_duration = np.random.randint(
                    max(min_mock_duration, int(original_duration * 0.5)),
                    max_mock_duration + 1,
                )
            elif original_duration > 15:
                mock_duration = np.random.randint(
                    max(min_mock_duration, int(original_duration * 0.3)),
                    max_mock_duration + 1,
                )
            else:
                mock_duration = np.random.randint(
                    max(min_mock_duration, int(original_duration * 0.2)),
                    max_mock_duration + 1,
                )

            mock_duration = max(min_mock_duration, mock_duration)

            # Generate a new start date within the allowed range
            new_start_date = row["start_date"] + pd.DateOffset(
                days=np.random.randint(1, mock_duration + 1) - 1
            )
            new_end_date = new_start_date + pd.DateOffset(days=mock_duration - 1)

            if new_start_date < row["start_date"] or new_end_date > row["end_date"]:
                attempts += 1
                continue

            # Ensure the mock campaign respects the min_days_gap constraint
            start_date_gap = (new_start_date - row["start_date"]).days
            end_date_gap = (row["end_date"] - new_end_date).days

            if start_date_gap < min_days_gap and end_date_gap < min_days_gap:
                attempts += 1
                continue

            # Ensure there is not too much overlap with the other (mock) campaigns
            if not too_much_overlap:
                for existing_mock in current_campaign_mocks:
                    overlap_days = max(
                        0,
                        (
                            min(existing_mock["end_date"], new_end_date)
                            - max(existing_mock["start_date"], new_start_date)
                        ).days
                        + 1,
                    )
                    if (
                        overlap_days / existing_mock["campaign_duration"]
                    ) > max_allowed_overlap:
                        too_much_overlap = True

            if not too_much_overlap:
                new_mock = {
                    "flight_id": f"mock_{row['flight_id']}_{num_mock_campaigns + 1}",
                    "start_date": new_start_date,
                    "end_date": new_end_date,
                    "advertiser": row["advertiser"],
                    "product": row["product"],
                    "campaign_duration": mock_duration,
                    "mock_campaign": True,
                }

                current_campaign_mocks.append(new_mock)
                num_mock_campaigns += 1
                attempts = 0  # Reset attempts if a mock campaign is successfully added
            else:
                attempts += 1

        new_mock_campaigns.extend(current_campaign_mocks)

    return pd.DataFrame(new_mock_campaigns)


def calculate_grps_for_mock_campaigns(df_mocks, df_spots):
    # Merge spots_df and campaigns_df based on advertiser and product
    merged_df = pd.merge(df_spots, df_mocks, on=["advertiser", "product"])
    # Filter rows where date is within start_date and end_date
    filtered_df = merged_df[
        (merged_df["date"] >= merged_df["start_date"])
        & (merged_df["date"] <= merged_df["end_date"])
    ]
    aggregated_df = (
        filtered_df.groupby("flight_id")
        .agg(
            {
                "npo1_grp": "sum",
                "npo2_grp": "sum",
                "npo3_grp": "sum",
                "regio_grp": "sum",
                "ster_grp": "sum",
            }
        )
        .reset_index()
    )
    final_campaigns_df = pd.merge(df_mocks, aggregated_df, on="flight_id", how="left")
    final_campaigns_df = final_campaigns_df.dropna(subset=["ster_grp"])

    return final_campaigns_df
