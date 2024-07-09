
import camp_tv_new.src.utils.bereik_utils as bereik_utils
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.database_utils as db_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func
import camp_tv_new.src.utils.dictionaries as mydict
from camp_tv_new.src.utils.query_dict import query_dict
import pandas as pd
import time
from tqdm import tqdm
import requests
import json

logger = setup_logger()

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
        "report": 'JordyCampBereik',
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
        json=dict_call
    )


    data = json.loads(res.text)[1]["Pivot"]["items"]
    if isinstance(data, list) and not data:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(data)

    return df


if __name__ == "__main__":

    # query = '''
    #     WITH RankedGroups AS (
    #     SELECT
    #         *,
    #         ROW_NUMBER() OVER (PARTITION BY target_group ORDER BY target_group) AS rn
    #     FROM
    #         [dbo].[tv.bereik]
    #     )
    #     SELECT
    #     *
    #     FROM
    #     RankedGroups
    #     WHERE
    #     rn = 1;
    # '''

    # df = db_utils.query_to_df(query)
    # print(df)

    rename_dict= {
        'DAG 25-59: DAG25-59',
        }

    tg = 'DAG 25-59'
    start_date = '010124'
    end_date = '070124'
    advertiser = 'Albert Heijn'
    product = 'Albert Heijn'
    token = api_utils.get_api_token()

    target_groups = mydict.target_groups

    for tg in target_groups:
        df = call_bereik_report_tv(tg, start_date, end_date, token, advertiser, product)

    # df = call_bereik_report_tv(tg, start_date, end_date, token, advertiser, product)