import camp_tv_new.src.utils.api_utils as api_utils
from camp_tv_new.src.utils.logger import setup_logger, log_warning_to_excel
import camp_tv_new.src.utils.dictionaries as mydict

import ast
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)

logger = setup_logger()

# from line_profiler import LineProfiler
# lp = LineProfiler()

def get_bereik(index, row, token: str):
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
    target_groups = row["missing_target_groups"]

    df = api_utils.call_bereik_report_tv(target_groups, start_date, end_date, token, advertiser, product)
    if df.empty is True:
        # logger.warning(f"Skipping row due to df being empty, for flight {flight_id}, advertiser {advertiser}, product {product}, start_date {start_date}, end_date {end_date}")
        log_warning_to_excel(flight_id, advertiser, product, start_date, end_date)
        return pd.DataFrame()

    df.rename(columns={0: 'advertiser', 1: 'product', 2: 'daypart'}, inplace=True)
    df.insert(0, "flight_id", str(flight_id))
    df.insert(1, "start_date", str(start_date))
    df.insert(2, "end_date", str(end_date))

    return df

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
        column_name = f"{first_part}_{third_part}_{second_part.strip().lower()}"
        # Add the value to the new row
        new_row[column_name] = float(value)
    return new_row

def transform_df(df):
    # Get the base columns and the target group columns
    base_columns = df.columns[:6].tolist()
    target_columns = df.columns[6:]

    # Dictionary to hold the new rows
    new_rows = []

    # Process each target group
    for target_group in set(col.split('_')[0] for col in target_columns):

        # Create a mask for the columns of the current target group
        target_cols = [col for col in target_columns if col.startswith(target_group)]

        # Iterate over the rows and duplicate them for each target group
        for _, row in df.iterrows():
            new_row = row[base_columns].copy()
            new_row['target_group'] = target_group

            # Add the corresponding values without the target group prefix
            for col in target_cols:
                new_col_name = '_'.join(col.split('_')[1:])
                new_row[new_col_name] = row[col]

            new_rows.append(new_row)

    return pd.DataFrame(new_rows)

def ensure_columns(df, column_order):
    # Add missing columns with default value 0
    for col in column_order:
        if col not in df.columns:
            df[col] = 0.0

    # Reorder columns according to column_order
    df = df[column_order]
    return df

def change_column_order(df):

    column_order = ['flight_id', 'target_group', 'campaign_duration','daypart', 'total_grp', 'ster_grp', 'regio_grp',
                    # 'talpa_grp', 'adalliance_grp',
                    'npo1_grp', 'npo2_grp', 'npo3_grp',
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
                    'regio_1+', 'regio_2+', 'regio_3+', 'regio_4+', 'regio_5+', 'regio_6+', 'regio_7+', 'regio_8+', 'regio_9+', 'regio_10+',
                    'ster_1+', 'ster_2+', 'ster_3+', 'ster_4+', 'ster_5+', 'ster_6+', 'ster_7+', 'ster_8+', 'ster_9+', 'ster_10+',
                    # 'talpa_1+', 'talpa_2+', 'talpa_3+', 'talpa_4+', 'talpa_5+', 'talpa_6+', 'talpa_7+', 'talpa_8+', 'talpa_9+', 'talpa_10+',
                    # 'adalliance_1+', 'adalliance_2+', 'adalliance_3+', 'adalliance_4+', 'adalliance_5+', 'adalliance_6+', 'adalliance_7+', 'adalliance_8+', 'adalliance_9+', 'adalliance_10+',
                    'total_1+', 'total_2+', 'total_3+', 'total_4+', 'total_5+', 'total_6+', 'total_7+', 'total_8+', 'total_9+', 'total_10+']

    df = ensure_columns(df, column_order)

    return df

def calculate_campaign_duration(row):
    start_date = pd.to_datetime(row['start_date'], format='%d%m%y')
    end_date = pd.to_datetime(row['end_date'], format='%d%m%y')
    return (end_date - start_date).days + 1

def process_raw_bereik_data(df_bereik_raw):
    # Process raw data from api
    processed_rows = [process_row(row) for _, row in df_bereik_raw.iterrows()]
    processed_rows = pd.DataFrame(processed_rows)
    processed_df = transform_df(processed_rows)

    # Calculate campaign duration
    processed_df['campaign_duration'] = processed_df.apply(lambda row: calculate_campaign_duration(row), axis=1)
    # Change column order
    processed_df = change_column_order(processed_df)
    # Rename target_groups back to normal syntax
    processed_df['target_group'] = processed_df['target_group'].replace(mydict.rename_dict)

    return processed_df