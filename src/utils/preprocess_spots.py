import utils.connection_utils as con_utils
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from icecream import ic
import os

from utils.logger import setup_logger
logger = setup_logger()

def check_file_existence(file_path):
    # Check if the file exists at the specified path
    if os.path.exists(file_path):
        # If the file exists, print a message indicating its existence
        logger.debug(f"The file '{file_path}' already exists.")
        return True
    else:
        # Check if the file exists in any subdirectories
        for root, dirs, files in os.walk(os.path.dirname(file_path)):
            for file in files:
                if file == os.path.basename(file_path):
                    # If the file exists in a subdirectory, print a message
                    logger.debug(f"The file '{file_path}' already exists in the subfolder '{root}'.")
                    return True
    # If the file does not exist in the specified path or any subdirectories, return False
    return False

def tv_clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Change Dutch annotations of numerics to American/English
    Remove rows where the sum of 'grp' columns is 0
    Remove rows where 'ster_id' is '-'
    Remove rows where 'advertiser' is '-none-'
    """
    for col in [col for col in df.columns if "grp" in col]:
        df[col] = df[col].apply(lambda row: row[3])
        df[col] = (df[col].str.replace(r"[^\d,]", "").str.replace(",", ".", regex=False).astype(float))

    df = df[df[[col for col in df.columns if "grp" in col]].sum(axis=1) != 0.0].reset_index(drop=True)

    df = df[df['advertiser'] != '-none-']

    return df


def change_hours_and_dates(df) -> pd.DataFrame:
    """
    Change the hours and dates in the given DataFrame.
    """
    # Convert date column to datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # Handle special cases where the hour is "24:00:00" or "25:00:00"
    df.loc[df['hour'] == '24:00:00', 'date'] += pd.to_timedelta(1, unit='d')
    df.loc[df['hour'] == '25:00:00', 'date'] += pd.to_timedelta(1, unit='d')

    # Replace "24:00:00" and "25:00:00" with "00:00:00" and "01:00:00" respectively
    df['hour'] = df['hour'].str.replace('24:00:00', '00:00:00').str.replace('25:00:00', '01:00:00')

    return df


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
    group_cols = ["date", "advertiser", "product", "daypart", "hour"]
    sum_cols = ["npo_1_grp", "npo_2_grp", "npo_3_grp", "ster_grp", "adalliance_grp", "talpa_grp", "total_grp",]
    df = df.groupby(by=group_cols)[sum_cols].sum().reset_index()

    return df


### Used for Spots Duration CAMP Prognose ###
# regio


# def preprocess_spots_duration(df):
#     """
#     Preprocess the given DataFrame by modifying column values, renaming columns,
#     fixing data types, removing NaN values, and sorting the DataFrame. 

#     Parameters:
#         df (pandas.DataFrame): The input dataframe from SpotTrackerJordy API Call
#     """
#     # Rename columns
#     df.columns = ['Datum', 'Tijd', 'Zender', 'Adverteerder', 'Product', 'Duur (sec)', 'STER ID', 'Kdh A6+', 'Kdh000 A6+']

#     # Extract last character from columns
#     df[['Kdh A6+', 'Kdh000 A6+']] = df[['Kdh A6+', 'Kdh000 A6+']].map(lambda x: x[-1]).astype(float)
#     df.reset_index(drop=True, inplace=True)

#     # Fix data types, remove NaN values, and sort
#     df[['Adverteerder', 'STER ID']] = df[['Adverteerder', 'STER ID']].astype(str)
#     df = df[(df['Adverteerder'] != '-none-') & (df['STER ID'] != 'nan')]
#     df['ster_id'] = df['STER ID'].apply(lambda x: x[:-2])

#     df = df.sort_values(by=['ster_id', 'Adverteerder', 'Datum']).reset_index(drop=True)
#     df['Datum'] = pd.to_datetime(df['Datum'])
#     df['Duur (sec)'] = df['Duur (sec)'].astype(int)

#     return df


# def spots_segment_campaigns_by_new_start(df):
#     """
#     Calculates the differences between spots in the given dataframe and assigns 
#     the result to new columns. Returns the modified dataframe.
#     """
#     # Calculate how many days between current date and last date
#     df['difference_last'] = abs(df['Datum'] - df['Datum'].shift(1)).dt.days.fillna(0).astype(int)

#     # New_start = start of a 'new' campaign, either because advertisers don't match or more than 8 days between dates
#     df['new_start'] = (df['difference_last'] > 8) | (df['Adverteerder'] != df['Adverteerder'].shift(1))

#     df["new_start"] = df["new_start"].astype(str)
#     df.loc[df['new_start'] == 'True', 'new_start'] = range(1, (df['new_start'] == 'True').sum() + 1)
#     df['new_start'] = np.where(df['new_start'] == 0, np.nan, df['new_start'])
#     df['new_start'] = pd.to_numeric(df['new_start'], errors='coerce').ffill().astype('Int64')

#     return df

# def get_unique_days(df):
#     df_unique_days = df.groupby(['new_start', 'ster_id'])['Datum'].nunique().to_frame().rename(columns={'Datum': 'unique_days'})
#     df_unique_days = df_unique_days.reset_index()

#     df_unique_days['start_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].min().tolist()
#     df_unique_days['end_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].max().tolist()

#     df_unique_days['date'] = df_unique_days[['start_date', 'end_date']].apply(
#         lambda x: '{}-{}'.format(datetime.strftime(x['start_date'], '%d%m%y'), datetime.strftime(x['end_date'], '%d%m%y')), axis=1)

#     return df_unique_days


# def delete_non_ster(df_spots: pd.DataFrame) -> pd.DataFrame:
#     """
#     Function to delete advertiser and/or product with no Ster GRP's.
#     It will delete the >>days<< where Ster GRP's are 0. This will make certain that flights with Ster GRP's and flights without, for the same advertiser/product, will be seperated.
#     For example: if you only delete advertisers with no GRP's, there still might be advertisers that have certain flights without Ster GRP's.

#     Parameters:
#     - df: the input dataframe to pivot. This is the df_spots generated by the get_new_spots script
#     Return:
#     - df_spots without non ster GRP's
#     """
#     sum_cols = ['npo_1_grp', 'npo_2_grp', 'npo_3_grp', 'ster_grp', 'adalliance_grp', 'talpa_grp', 'total_grp']
#     df_pivot = df_spots.groupby(['advertiser', 'product', 'date'])[sum_cols].sum().reset_index()

#     # Identify rows where 'ster_grp' is 0 for a single day.
#     df_pivot = df_pivot[df_pivot['ster_grp'] != 0]

#     return df_pivot

# endregion