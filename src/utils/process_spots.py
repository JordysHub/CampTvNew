import utils.connection_utils as con_utils
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

import os
import ast

from utils.logger import setup_logger
logger = setup_logger()

def determine_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Params:
        df: DataFrame - the input DataFrame containing advertiser, product, and exploitant groups.
    Returns:
        DataFrame - the DataFrame with advertiser, product, and exploitant ids.
    """

    df_ids = pd.DataFrame(df[["advertiser", "product"]])
    df_ids = df_ids.drop_duplicates().set_index(["advertiser", "product"])

    # Get all unique values of ids per exploitant
    for expl in ["ster", "adalliance", "talpa"]:
        df_ids = df_ids.merge(df[df[f"{expl}_grp"] > 0]
                              .groupby(["advertiser", "product"])["ster_id"]
                              .apply(lambda x: ",".join(x.unique())).to_frame()
                              .rename(columns={"ster_id": f"{expl}_ids"}),
                              how="left",
                              left_index=True,
                              right_index=True,
                              ).fillna("")

    df_ids = df_ids.reset_index()

    return df_ids


def add_dayparts(df: pd.DataFrame) -> pd.DataFrame:
    """
    A function to add periods/dayparts to the dataframe and perform groupby and sum operation.
    """
    # create periods/dayparts
    df["daypart"] = (df["hour"]
                     .isin([f"{x}:00:00" for x in range(18, 24)])
                     .map({True: "primetime", False: "day&night"})
                     )

    # Perform the groupby and sum operation
    group_cols = ['date', 'advertiser', 'product', 'daypart', 'hour']
    sum_cols = ['npo1_grp', 'npo2_grp', 'npo3_grp', 'ster_grp', 'regio_grp', 'adalliance_grp', 'talpa_grp', 'total_grp']
    df = df.groupby(by=group_cols)[sum_cols].sum().reset_index()

    return df


def convert_to_list(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return string  # Return as is if not convertible to list

def process_row(row):
    new_row = row[:5].to_dict()
    for col_idx, cell in enumerate(row[5:], start=6):
        if isinstance(cell, float) and np.isnan(cell):
            continue
        # Extract information from the list
        cell = convert_to_list(cell)
        first_part, second_part, third_part, value = cell
        # Generate column name based on second value in the list
        if second_part.endswith(' (%)'):
            second_part = second_part.split(' ')[0]
        else:
            second_part = 'grp'
        third_part = third_part.strip().replace(" ", "").lower()
        column_name = f"{third_part}_{second_part.strip().lower()}"
        # Add the value to the new row
        new_row[column_name] = float(value)
    return new_row

def process_spots_day(df, day):
    processed_rows = [process_row(row) for _, row in df.iterrows()]
    df = pd.DataFrame(processed_rows).fillna(0)
    if day < datetime(2024, 1, 1):
        df['regio_grp'] = 0

    new_column_names = ['date', 'advertiser', 'product', 'hour', 'ster_id']
    df.columns = new_column_names + list(df.columns[5:])

    df_ids = determine_ids(df)
    df = add_dayparts(df)
    df = df.merge(df_ids, on=["advertiser", "product"], how="left").sort_values(by=["date", "advertiser"])
    df = df[df['advertiser'] != '-none-']

    return df
def clean_hour_column(df):

    df['hour'] = df['hour'].str.replace('24:00:00', '00:00:00').str.replace('25:00:00', '01:00:00')
    df['hour'] = pd.to_datetime(df['hour'], format='%H:%M:%S')

    return df
def count_spots_and_grp(df):

    grouped_df = df.groupby(['advertiser', 'product', 'date']).agg(
        spot_count=('advertiser', 'size'),
        npo1_grp=('npo1_grp', 'sum'),
        npo2_grp=('npo2_grp', 'sum'),
        npo3_grp=('npo3_grp', 'sum'),
        ster_grp=('ster_grp', 'sum'),
        regio_grp=('regio_grp', 'sum'),
        adalliance_grp=('adalliance_grp', 'sum'),
        talpa_grp=('talpa_grp', 'sum'),
        total_grp=('total_grp', 'sum')).reset_index()

    return grouped_df.sort_values(by=['date', 'advertiser', 'product'])