import requests
from requests.auth import HTTPBasicAuth
import camp_tv_new.src.utils.dictionaries as dict
from datetime import datetime, date
import pandas as pd
import os
import argparse
import json
from icecream import ic
from dotenv import load_dotenv
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger()

def get_api_token() -> str:
    req = requests.post(
        "https://auth.grouptechedge.com/connect/token",
        auth=HTTPBasicAuth("client.ster", os.getenv("EDGEAPI")),
        data={"grant_type": "client_credentials"},
    )
    token = json.loads(req.content)["access_token"]

    return token

def valid_date(s):
    try:
        parsed_date = datetime.strptime(s, "%d%m%y")
        return parsed_date.strftime("%d%m%y")  # Return the date as a string
    except ValueError:
        msg = "Not a valid date: '{0}'. Should be DDMMYY".format(s)
        logger.debug(msg)  # Log error message as a debug message
        raise argparse.ArgumentTypeError(msg)


# def get_last_known_date_offline(root_folder) -> date:
#     """
#     Retrieve the last known date from local files
#     """
#     try:
#         latest_year = max(os.listdir(root_folder))
#         latest_month = max(os.listdir(os.path.join(root_folder, latest_year)))
#         month_folder = os.path.join(root_folder, latest_year, latest_month)

#         latest_file = None
#         latest_date = None

#         for file_name in os.listdir(month_folder):
#             if file_name.endswith('.xlsx'):
#                 file_path = os.path.join(month_folder, file_name)
#                 file_date = os.path.getmtime(file_path)
#                 if latest_date is None or file_date > latest_date:
#                     latest_date = file_date
#                     latest_file = file_name

#         full_path = os.path.join(root_folder, latest_year, latest_month, os.path.splitext(latest_file)[0])
#         folder_path = full_path.replace('\\', '/')
#         parts = folder_path.split('/')

#         year = parts[-3]
#         month = parts[-2]
#         day = parts[-1]

#         date_str = f"{day}{month}{year}"
#         date = datetime.strptime(date_str, '%d%m%Y')

#     # return the default date if no files are found, so it will fetch from 01-09-23 and onwards
#     except:
#         default_date = datetime(2023, 8, 31)
#         return default_date, ""

#     return date, folder_path + '.xlsx'

def call_bereik_report_tv(target_group: str, start_date: str, end_date: str, token: str, advertiser=None, product=None) -> pd.DataFrame:
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
    target_group = dict.rename_dict.get(target_group, target_group)

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
        "report": 'JordyCampBereik',
        "period": f"{start_date}-{end_date}",
        "filtertext": filter_text,
    }

    res = requests.post(
        "https://sternl.iea.grouptechedge.com/api/advantedge",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=dict_call
    )

    data = json.loads(res.text)[1]["Pivot"]["items"]
    if isinstance(data, list) and not data:
        df = pd.DataFrame()
    else: 
        df = pd.DataFrame(data)

    return df

def call_kdh_getter_report(day: str, token: str) -> pd.DataFrame:
    """
    Call the kdh (kijkdichtheid) getter report for tv. The call is made per day for all spots in this script.
    """
    # transform period day to string in DDMMYY format
    res = requests.post(
        "https://sternl.iea.grouptechedge.com/api/advantedge",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "report": "camp_kdh_getter",
            "target": "10+",
            "period": f"{day}",
        },
    )

    try:
        data = json.loads(res.text)[1]["Pivot"]["items"]
        df = pd.DataFrame(data,
                          columns=[
                              "date",
                              "advertiser",
                              "product",
                              "hour",
                              "ster_id",
                              "npo_1_grp",
                              "npo_2_grp",
                              "npo_3_grp",
                              "ster_grp",
                              "adalliance_grp",
                              "talpa_grp",
                              "total_grp"])
        assert not df.empty, logger.debug(f"DataFrame from API is empty for given day, {day}.")

    except (KeyError, IndexError, ValueError) as e:
        logger.error(e)
        df = pd.DataFrame()

    return df
