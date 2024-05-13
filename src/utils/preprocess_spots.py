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

def get_last_known_date_offline(spots_folder) -> date:
    """
    Retrieve the last known date from local files
    """

    latest_day = None
    latest_date = None

    for year_folder in os.listdir(spots_folder):
        year_path = os.path.join(spots_folder, year_folder)
        if not os.path.isdir(year_path):
            continue

        for month_folder in os.listdir(year_path):
            month_path = os.path.join(year_path, month_folder)
            if not os.path.isdir(month_path):
                continue

            for day_folder in os.listdir(month_path):
                day_path = os.path.join(month_path, day_folder)
                if not os.path.isdir(day_path):
                    continue

                day_date = int(day_folder)
                if latest_date is None or day_date > latest_date:
                    latest_date = day_date
                    latest_day = day_path

    return latest_day

def get_last_known_date(query: str) -> date:
    """
    Retrieve the last known date based on the provided query and add 1 day (t+1).
    Args: query (str): The query used to retrieve the date.
    Returns: date: The last known date in database + 1 day.
    """
    date_str = con_utils.execute_query_to_df(query).iloc[0, 0]
    start_date = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)

    return start_date

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
    group_cols = ["date", "advertiser", "product", "daypart"]
    sum_cols = ["npo_1_grp", "npo_2_grp", "npo_3_grp", "ster_grp", "adalliance_grp", "talpa_grp", "total_grp",]
    df = df.groupby(by=group_cols)[sum_cols].sum().reset_index()

    return df


### Used for Spots Duration CAMP Prognose ###
# regio


def preprocess_spots_duration(df):
    """
    Preprocess the given DataFrame by modifying column values, renaming columns,
    fixing data types, removing NaN values, and sorting the DataFrame. 

    Parameters:
        df (pandas.DataFrame): The input dataframe from SpotTrackerJordy API Call
    """
    # Rename columns
    df.columns = ['Datum', 'Tijd', 'Zender', 'Adverteerder', 'Product', 'Duur (sec)', 'STER ID', 'Kdh A6+', 'Kdh000 A6+']

    # Extract last character from columns
    df[['Kdh A6+', 'Kdh000 A6+']] = df[['Kdh A6+', 'Kdh000 A6+']].map(lambda x: x[-1]).astype(float)
    df.reset_index(drop=True, inplace=True)

    # Fix data types, remove NaN values, and sort
    df[['Adverteerder', 'STER ID']] = df[['Adverteerder', 'STER ID']].astype(str)
    df = df[(df['Adverteerder'] != '-none-') & (df['STER ID'] != 'nan')]
    df['ster_id'] = df['STER ID'].apply(lambda x: x[:-2])

    df = df.sort_values(by=['ster_id', 'Adverteerder', 'Datum']).reset_index(drop=True)
    df['Datum'] = pd.to_datetime(df['Datum'])
    df['Duur (sec)'] = df['Duur (sec)'].astype(int)

    return df


def spots_segment_campaigns_by_new_start(df):
    """
    Calculates the differences between spots in the given dataframe and assigns 
    the result to new columns. Returns the modified dataframe.
    """
    # Calculate how many days between current date and last date
    df['difference_last'] = abs(df['Datum'] - df['Datum'].shift(1)).dt.days.fillna(0).astype(int)

    # New_start = start of a 'new' campaign, either because advertisers don't match or more than 8 days between dates
    df['new_start'] = (df['difference_last'] > 8) | (df['Adverteerder'] != df['Adverteerder'].shift(1))

    df["new_start"] = df["new_start"].astype(str)
    df.loc[df['new_start'] == 'True', 'new_start'] = range(1, (df['new_start'] == 'True').sum() + 1)
    df['new_start'] = np.where(df['new_start'] == 0, np.nan, df['new_start'])
    df['new_start'] = pd.to_numeric(df['new_start'], errors='coerce').ffill().astype('Int64')

    return df


def count_spots(df):
    df_spots = df.groupby(['new_start', 'ster_id'])['Zender'].count().reset_index()
    df_spots.rename(columns={'Zender': 'spots'}, inplace=True)
    df_spots['start_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].min().tolist()
    df_spots['end_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].max().tolist()
    df_spots['date'] = df_spots[['start_date', 'end_date']].apply(
        lambda x: '{}-{}'.format(datetime.strftime(x['start_date'], '%d%m%y'), datetime.strftime(x['end_date'], '%d%m%y')), axis=1)

    return df_spots


def get_unique_days(df):
    df_unique_days = df.groupby(['new_start', 'ster_id'])['Datum'].nunique().to_frame().rename(columns={'Datum': 'unique_days'})
    df_unique_days = df_unique_days.reset_index()

    df_unique_days['start_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].min().tolist()
    df_unique_days['end_date'] = df.groupby(['new_start', 'ster_id'])['Datum'].max().tolist()

    df_unique_days['date'] = df_unique_days[['start_date', 'end_date']].apply(
        lambda x: '{}-{}'.format(datetime.strftime(x['start_date'], '%d%m%y'), datetime.strftime(x['end_date'], '%d%m%y')), axis=1)

    return df_unique_days


def delete_non_ster(df_spots: pd.DataFrame) -> pd.DataFrame:
    """
    Function to delete advertiser and/or product with no Ster GRP's.
    It will delete the >>days<< where Ster GRP's are 0. This will make certain that flights with Ster GRP's and flights without, for the same advertiser/product, will be seperated.
    For example: if you only delete advertisers with no GRP's, there still might be advertisers that have certain flights without Ster GRP's.

    Parameters:
    - df: the input dataframe to pivot. This is the df_spots generated by the get_new_spots script
    Return:
    - df_spots without non ster GRP's
    """
    sum_cols = ['npo_1_grp', 'npo_2_grp', 'npo_3_grp', 'ster_grp', 'adalliance_grp', 'talpa_grp', 'total_grp']
    df_pivot = df_spots.groupby(['advertiser', 'product', 'date'])[sum_cols].sum().reset_index()

    # Identify rows where 'ster_grp' is 0 for a single day.
    df_pivot = df_pivot[df_pivot['ster_grp'] != 0]

    return df_pivot

# endregion


### Inkoop opties Functions ###
# region

def normalize_camps_channels(df):

    # Normalize inzet campagnes over channels
    df_channels = df.groupby(['new_start', 'Zender'])['Kdh A6+'].sum().unstack(-1).fillna(0)
    df_channels = df_channels.rename_axis(None, axis=1).fillna(0)
    df_channels = df_channels.div(df_channels.sum(axis=1), axis=0).round(2)

    return df_channels


def get_inkoop(df, df_channels):

    df['primetime'] = df['Tijd'].apply(lambda x: x > x.replace(hour=18, minute=0, second=0))
    df_primetime = df.groupby(['new_start'])['primetime'].mean().to_frame()
    df_primetime_channels = df.groupby(['new_start', 'Zender'])['primetime'].mean().unstack(-1).rename_axis(None, axis=1).fillna(0)
    df_primetime_channels.columns = ['NPO 1_primetime', 'NPO 2_primetime', 'NPO 3_primetime']
    df_ink = df_channels.merge(df_primetime, how='left', left_index=True, right_index=True)
    df_ink = df_ink.merge(df_primetime_channels, how='left', left_index=True, right_index=True)

    df_ink['inkoopoptie_primetime'] = df_ink['primetime']
    df_ink['inkoopoptie_day&night'] = 1 - df_ink['primetime']
    df_ink['selectpakket_jong_volwassenen'] = df_ink['NPO 3_primetime']
    df_ink['selectpakket_senioren'] = (df_ink['NPO 3'] < 0.1) & (df_ink['NPO 1_primetime'] < 0.15)
    df_ink['selectpakket_zakelijk'] = ((df_ink['NPO 1_primetime'] > 0.8) | (df_ink['NPO 2_primetime'] > 0.8)) & (df_ink['NPO 3'] < 0.1)
    df_ink['selectpakket_jeugd'] = (df_ink['NPO 3'] > 0.85) & (df_ink['NPO 3_primetime'] < 0.25)

    return df_ink


def second_spot_duration(spots_dur_list):
    if len(spots_dur_list) > 1:
        spots_dur_list.remove(max(spots_dur_list))
        if max(spots_dur_list) <= 10:
            return 0
        else:
            return max(spots_dur_list)
    else:
        return 0


def get_spot_tagons(df):
    df_tag = df.groupby(['new_start'])['Duur (sec)'].unique().to_frame()
    df_tag['hoofdspot_duration'] = df_tag['Duur (sec)'].apply(lambda x: max(x))
    df_tag['tagon'] = df_tag['Duur (sec)'].apply(lambda x: (len(x) > 1) & ((5 | 10) in x))
    df_tag['second_spot_duration'] = df_tag['Duur (sec)'].apply(lambda x: second_spot_duration(list(x)))
    df_tag = df_tag[['hoofdspot_duration', 'second_spot_duration', 'tagon']].reset_index()

    return df_tag


def clean_dataframe(df):
    """
    Cleans the input dataframe by removing duplicates, calculating duration days, and adjusting end dates based on specified conditions. 
    """

    first_date_list = df.groupby(['new_start'])['Datum'].min().tolist()
    last_date_list = df.groupby(['new_start'])['Datum'].max().tolist()

    df = df.drop_duplicates(subset=['new_start'], keep='first').reset_index(drop=True)

    df['start_date'] = first_date_list
    df['end_date'] = last_date_list

    df['duration_days'] = (df['start_date'] - df['end_date']).dt.days.abs()

    df.loc[((df['duration_days'].shift(-1) < 3) & (df['difference_last'].shift(-1) < 10)),
           'end_date'] = df.loc[((df['duration_days'] < 3) & (df['difference_last'] < 10)), 'end_date'].tolist()
    df = df.loc[~((df['duration_days'] < 3) & (df['difference_last'] < 10)), :]

    df['start_date'] = df['start_date'].dt.date
    df['end_date'] = df['end_date'].dt.date

    df = df[['start_date', 'end_date'] + [col for col in df.columns if col not in ['start_date', 'end_date']]]

    return df


def merge_dataframes(df, df_inkoop, df_tag):

    df = df.merge(df_inkoop[[x for x in df_inkoop.columns if ('inkoopoptie' in x) | ('selectpakket' in x)]], on=['new_start'], how='left')
    df = df.merge(df_tag, on=['new_start'], how='left')
    # Drop unnecessary columns
    df.drop(columns=['Datum', 'new_start'], inplace=True)

    return df


def add_alcohol_kansspelen(df):
    df_alc_kans = pd.read_excel('./data/interim/alcohol_kansspelen_adverteerders.xlsx')
    df['alcohol_adv'] = df['Adverteerder'].isin(df_alc_kans[df_alc_kans['Categorie'] == 'Alcohol']['Adverteerder']) & df['Product'].isin(
        df_alc_kans[df_alc_kans['Categorie'] == 'Alcohol']['Product'])
    df['kansspelen_adv'] = df['Adverteerder'].isin(df_alc_kans[df_alc_kans['Categorie'] == 'Kansspelen']['Adverteerder']) & df['Product'].isin(
        df_alc_kans[df_alc_kans['Categorie'] == 'Kansspelen']['Product'])

    return df
