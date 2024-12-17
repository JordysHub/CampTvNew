import src.utils.bereik_utils as bereik_utils
import src.utils.api_utils as api_utils
import src.utils.database_utils as db_utils
# from src.utils.logger import setup_logger, timer_func
import src.utils.dictionaries as mydict
from src.utils.query_dict import query_dict

import pandas as pd
import time
from tqdm import tqdm
import requests
import json
import ast
import numpy as np

# logger = setup_logger()


# def retrieve_and_format_flights(query_key):
#     df = db_utils.query_to_df(query_dict[query_key])
#     df["start_date"] = pd.to_datetime(df["start_date"]).dt.strftime("%d%m%y")
#     df["end_date"] = pd.to_datetime(df["end_date"]).dt.strftime("%d%m%y")
#     return df


def call_bereik_report_tv(
    target_group: str,
    start_date: str,
    end_date: str,
    token: str,
    advertiser=None,
    product=None,
) -> pd.DataFrame:
    """
    Call the camp bereik getter report API, retrieve the data for the specified target group, advertiser, product, start date, and end date, and return the result as a DataFrame.
    Advertiser and product aren't strictly nesssary, so the report can be called without these.

    Parameters:
    - target_group: the target group for the report
    - start_date: the start date in string format %d%m%y
    - end_date: the end date in string format %d%m%y
    - token: the authorization token for the API request
    - advertiser: the advertiser string
    - product: product string
    - only_ster: if True, only STER channels are included in the report
    """
    # target_group = dict.rename_dict.get(target_group, target_group)

    if advertiser is not None:
        if product is not None:
            filter_text = f"Holland::Adverteerder::{advertiser}&&product::{product}"
        else:
            filter_text = f"Holland::Adverteerder::{advertiser}"
    elif product is not None:
        filter_text = f"product::{product}"
    else:
        filter_text = None

    dict_call = {
        "target": target_group,
        "report": "JordyCampBereik",
        "period": f"{start_date}-{end_date}",
        "filtertext": filter_text,
    }
    print(dict_call)

    res = requests.post(
        "https://sternl.iea.grouptechedge.com/api/advantedge",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=dict_call,
    )

    data = json.loads(res.text)[1]["Pivot"]["items"]
    if isinstance(data, list) and not data:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(data)

    return df


# def get_bereik(index, row, target_group, token: str):
#     """
#     Get the bereik report for a specific target group within a given date range.

#     Parameters:
#     - index: int, the index of the row
#     - row: pandas Series, the row containing flight information
#     - target_group: str, the target group for the report
#     - token: str, the API token for authentication

#     Returns:
#     - pandas DataFrame, the bereik report for the specified target group
#     """
#     flight_id = row["flight_id"]
#     advertiser = row["advertiser"]
#     product = row["product"]
#     start_date = row["start_date"]  # in DDMMYY format
#     end_date = row["end_date"]  # in DDMMYY format

#     df = api_utils.call_bereik_report_tv(
#         target_group, start_date, end_date, token, advertiser, product
#     )
#     if df.empty is True:
#         return pd.DataFrame()

#     df.rename(columns={0: "advertiser", 1: "product", 2: "daypart"}, inplace=True)
#     df.insert(0, "flight_id", str(flight_id))
#     df.insert(1, "start_date", str(start_date))
#     df.insert(2, "end_date", str(end_date))

#     return df


# def process_raw_bereik_data(df_bereik_raw):
#     # Process raw data from api
#     processed_rows = [process_row(row) for _, row in df_bereik_raw.iterrows()]
#     processed_df = pd.DataFrame(processed_rows).fillna(0)

#     return processed_df


# def convert_to_list(string):
#     try:
#         return ast.literal_eval(string)
#     except (ValueError, SyntaxError):
#         return string  # Return as is if not convertible to list


# def process_row(row):
#     new_row = row[:6].to_dict()
#     for _, cell in enumerate(row[6:], start=6):
#         if isinstance(cell, float) and np.isnan(cell):
#             continue
#         # Extract information from the list
#         cell = convert_to_list(cell)
#         first_part, second_part, third_part, value = cell
#         # Generate column name based on second value in the list
#         if second_part.endswith(" (%)"):
#             second_part = second_part.split(" ")[0]
#         else:
#             second_part = "grp"
#         third_part = third_part.strip().replace(" ", "").lower()
#         column_name = f"{first_part}_{third_part}_{second_part.strip().lower()}"
#         # Add the value to the new row
#         new_row[column_name] = float(value)
#     return new_row


# def transform_df(df):
#     # Get the base columns and the target group columns
#     base_columns = df.columns[:6].tolist()
#     target_columns = df.columns[6:]

#     # Dictionary to hold the new rows
#     new_rows = []

#     # Process each target group
#     for target_group in set(col.split("_")[0] for col in target_columns):
#         # Create a mask for the columns of the current target group
#         target_cols = [col for col in target_columns if col.startswith(target_group)]

#         # Iterate over the rows and duplicate them for each target group
#         for _, row in df.iterrows():
#             new_row = row[base_columns].copy()
#             new_row["target_group"] = target_group

#             # Add the corresponding values without the target group prefix
#             for col in target_cols:
#                 new_col_name = "_".join(col.split("_")[1:])
#                 new_row[new_col_name] = row[col]

#             new_rows.append(new_row)

#     # Create a new DataFrame from the new rows
#     new_df = pd.DataFrame(new_rows)

#     return new_df


# if __name__ == "__main__":

#     df_flights = retrieve_and_format_flights("get_flights")
#     df_flights = df_flights.iloc[:2]
#     target_groups = "25-67, B2B, 20-49"

#     current_token_time = time.time()
#     token = api_utils.get_api_token()

#     for _, row in tqdm(
#         df_flights.iterrows(),
#         total=len(df_flights),
#         position=0,
#         ncols=120,
#         bar_format="{desc}: {percentage:.0f}%|{bar}| {n}/{total} Elapsed: {elapsed} Remaining: {remaining}",
#     ):

#         if time.time() - current_token_time >= 3000:
#             logger.debug("Refreshing token...")
#             token = api_utils.get_api_token()
#             current_token_time = time.time()

#         flight_id = row["flight_id"]
#         advertiser = row["advertiser"]
#         product = row["product"]
#         start_date = row["start_date"]  # in DDMMYY format
#         end_date = row["end_date"]  # in DDMMYY format

#         df_bereik = get_bereik(row.name, row, target_groups, token)
#         df = process_raw_bereik_data(df_bereik)
#         df = transform_df(df)
#         df.to_excel(f"bereik_{target_groups}.xlsx", index=False)

#     print(df)

#     # query = '''
#     #     WITH RankedGroups AS (
#     #     SELECT
#     #         *,
#     #         ROW_NUMBER() OVER (PARTITION BY target_group ORDER BY target_group) AS rn
#     #     FROM
#     #         [dbo].[tv.bereik]
#     #     )
#     #     SELECT
#     #     *
#     #     FROM
#     #     RankedGroups
#     #     WHERE
#     #     rn = 1;
#     # '''

#     # df = db_utils.query_to_df(query)
#     # print(df)

#     """
#         rename_dict= {
#             'DAG 25-59: DAG25-59',
#             }

#         tg = 'DAG 25-59'
#         start_date = '010124'
#         end_date = '070124'
#         advertiser = 'Albert Heijn'
#         product = 'Albert Heijn'
#         token = api_utils.get_api_token()

#         target_groups = mydict.target_groups

#         for tg in target_groups:
#             df = call_bereik_report_tv(tg, start_date, end_date, token, advertiser, product)

#         # df = call_bereik_report_tv(tg, start_date, end_date, token, advertiser, product)

#     """
