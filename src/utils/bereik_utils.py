import camp_tv_new.src.utils.dictionaries as dict
import camp_tv_new.src.utils.api_utils as api_utils
from camp_tv_new.src.utils.logger import setup_logger

import ast
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)

logger = setup_logger()

# from line_profiler import LineProfiler
# lp = LineProfiler()

def get_bereik(index, row, target_group: str, token: str):
    """
    Get the bereik report for a specific target group within a given date range.

    Parameters:
    - index: int, the index of the row
    - row: pandas Series, the row containing flight information
    - target_group: str, the target group for the report
    - token: str, the API token for authentication

    Returns:
    - pandas DataFrame, the bereik report for the specified target group
    """
    flight_id = row["flight_id"]
    advertiser = row["advertiser"]
    product = row["product"]
    start_date = row["start_date"]  # in DDMMYY format
    end_date = row["end_date"]  # in DDMMYY format

    df = api_utils.call_bereik_report_tv(target_group, start_date, end_date, token, advertiser, product)
    if df.empty is True:
        logger.warning(f"Skipping row due to df being empty, for flight {flight_id}, advertiser {advertiser}, product {product}, start_date {start_date}, end_date {end_date}")
        return pd.DataFrame()

    df.rename(columns={0: 'advertiser', 1: 'product', 2: 'daypart'}, inplace=True)
    df.insert(0, "flight_id", str(flight_id))
    df.insert(1, "start_date", str(start_date))
    df.insert(2, "end_date", str(end_date))

    return df

def get_new_and_updated_flights(df_bereik, df_all_flights):
    df_bereik = df_bereik.iloc[:, :5].drop_duplicates(subset=['flight_id'])
    # get new flights
    new_flight_ids = df_all_flights[~df_all_flights['flight_id'].isin(df_bereik['flight_id'])]['flight_id'].to_list()
    # get updated flights
    merged_df = pd.merge(df_bereik, df_all_flights, on=['flight_id', 'advertiser', 'product'], suffixes=('_old', '_all'))
    filtered_df = merged_df[merged_df['end_date_all'] != merged_df['end_date_old']]
    updated_flight_ids = filtered_df['flight_id'].tolist()

    combined_flight_ids = new_flight_ids + updated_flight_ids
    combined_flight_ids = set(combined_flight_ids)

    return combined_flight_ids

def fetch_all_data_new_tg(df_all_flights, target_group, file_path):
    logger.info(f"Fetching all data for new target group {target_group}...")
    try:
        df_bereik = get_bereik(df_all_flights, target_group)
        df_bereik.to_excel(file_path, index=False)
    except Exception as e:
        logger.error(f"Error fetching data for new target group {target_group}: {str(e)}")

def convert_to_list(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return string  # Return as is if not convertible to list

def process_row(row):
    new_row = row[:6].to_dict()
    for col_idx, cell in enumerate(row[6:], start=6):
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


def change_column_order(df):

    column_order_first = ['flight_id', 'start_date', 'end_date', 'advertiser', 'product', 'daypart', 'total_grp', 'ster_grp', 'regio_grp', 'talpa_grp', 'adalliance_grp',
                          'npo1_grp', 'npo2_grp', 'npo3_grp',
                          'regiotvutrecht_grp', 'tvnoord-holland_grp', 'l1tv_grp', 'omroepbrabanttv_grp',	'tvflevoland_grp',
                          'tvzeeland_grp', 'tvgelderland_grp', 'tvoost_grp', 'tvdrenthe_grp', 'omropfryslantelevisie_grp', 'tvnoord_grp', 'tvrijmond_grp', 'tvwest_grp', 'at5_grp',
                          'npo1_1+', 'npo2_1+', 'npo3_1+',
                          'npo1_2+', 'npo2_2+', 'npo3_2+',
                          'npo1_3+', 'npo2_3+', 'npo3_3+',
                          'npo1_4+', 'npo2_4+', 'npo3_4+',
                          'npo1_5+', 'npo2_5+', 'npo3_5+',
                          'npo1_6+', 'npo2_6+', 'npo3_6+',
                          'npo1_7+', 'npo2_7+', 'npo3_7+',
                          'npo1_8+', 'npo2_8+', 'npo3_8+',
                          'npo1_9+', 'npo2_9+', 'npo3_9+',
                          'npo1_10+', 'npo2_10+', 'npo3_10+',
                          'ster_1+', 'ster_2+', 'ster_3+', 'ster_4+', 'ster_5+', 'ster_6+', 'ster_7+', 'ster_8+', 'ster_9+', 'ster_10+',
                          'regio_1+', 'regio_2+', 'regio_3+', 'regio_4+', 'regio_5+', 'regio_6+', 'regio_7+', 'regio_8+', 'regio_9+', 'regio_10+']

    column_order_with_total = [col for col in df.columns if 'total' in col and col not in column_order_first]
    column_order_with_adalliance = [col for col in df.columns if 'adalliance' in col and col not in column_order_first]
    column_order_with_talpa = [col for col in df.columns if 'talpa' in col and col not in column_order_first]

    columns_concat = column_order_first + column_order_with_total + column_order_with_adalliance + column_order_with_talpa
    desired_column_order = column_order_first + [col for col in df.columns if col not in columns_concat] + \
        column_order_with_adalliance + column_order_with_talpa + column_order_with_total

    return df[desired_column_order]
