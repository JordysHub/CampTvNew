from src.utils.logger import setup_logger

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import pandas as pd
import os
import argparse
import json
import time
from dotenv import load_dotenv

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


def call_pop_report_tv(target_group: str, token: str) -> pd.DataFrame:

    dict_call = {
        "target": target_group,
        "report": "JordyPop",
        "period": "-1d",
    }

    res = requests.post(
        "https://sternl.iea.grouptechedge.com/api/advantedge",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=dict_call,
    )

    data = json.loads(res.text)[1]["Pivot"]["items"]
    df = pd.DataFrame(data)

    return df


def call_bereik_report_tv(
    target_groups: str,
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
        "target": target_groups,
        "report": "JordyCampBereik",
        "period": f"{start_date}-{end_date}",
        "filtertext": filter_text,
    }

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


def call_kdh_getter_report(
    day: str, token: str, advertiser=None, product=None
) -> pd.DataFrame:
    """
    Call the kdh (kijkdichtheid) getter report for tv. The call is made per day for all spots in this script.
    """
    if advertiser is not None:
        if product is not None:
            filter_text = f"Holland::Adverteerder::{advertiser}&&product::{product}"
        else:
            filter_text = f"Holland::Adverteerder::{advertiser}"
    elif product is not None:
        filter_text = f"product::{product}"
    else:
        filter_text = None

    # transform period day to string in DDMMYY format
    res = requests.post(
        "https://sternl.iea.grouptechedge.com/api/advantedge",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "report": "Jordy_kdh_getter_nmo_Ster",
            "target": "10+",
            "period": f"{day}",
            "filtertext": filter_text,
        },
    )

    try:
        data = json.loads(res.text)[1]["Pivot"]["items"]
        df = pd.DataFrame(data)
        assert not df.empty, logger.debug(
            f"DataFrame from API is empty for given day, {day}."
        )

    except (KeyError, IndexError, ValueError) as e:
        logger.error(e)
        df = pd.DataFrame()

    return df


def retry_with_exponential_backoff(
    func, *args, retries=5, initial_wait=1, max_wait=60, **kwargs
):
    """
    Retry a function with exponential backoff.

    Parameters:
        func (callable): The function to be retried.
        retries (int): Number of retries.
        initial_wait (int): Initial wait time between retries.
        max_wait (int): Maximum wait time between retries.
    """
    wait = initial_wait
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                raise
            time.sleep(wait)
            wait = min(wait * 2, max_wait)
