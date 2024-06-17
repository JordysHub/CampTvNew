# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings
import camp_tv_new.src.utils.api_utils as api_utils

from dotenv import load_dotenv
from camp_tv_new.src.utils.logger import setup_logger, timer_func

import pandas as pd
import warnings

pd.set_option('future.no_silent_downcasting', True)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
# endregion

# Load environment variables: determines whether to retrieve data exclusively from Ster/NPO.
load_dotenv()
# setup logger
logger = setup_logger()

def calculate_pop(df):
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(
        lambda x: x.apply(lambda x: float(str(x[-1]))), axis=1)
    population = (100 / df.iloc[0, 1]) * (1000 * df.iloc[0, 2])
    population = round(population / 1000) * 1000

    return population

# '30-60EH', '35-59AB1'

if __name__ == "__main__":
    pop_dict = {}
    target_groups = ['13+', '20-49', '25+', '25-39', '25-54', '25-59', '25-59AB1', '25-67',
                     '25-67AB1', '3-12', '30-65', '35+', '35-59', '35-64', '50+', '6+', '68+', 
                     '7-12', 'BDS 25-59', 'BDS 25-67', 'B2B',
                     'BDS KZ12', 'BDS+KND', 'DAG 25-59', 'M 20-49', 'M 25-54', 'M 25-59',
                     'M 25-67', 'M 50+', 'V 20-49', 'V 25-54', 'V 25-59', 'V 25-67', 'V 40+',
                     'V 50+', 'W1 45-75']

    token = api_utils.get_api_token()
    for tg in target_groups:
        df = api_utils.call_pop_report_tv(tg, token)
        pop_dict[tg] = calculate_pop(df)

    pop_dict = {key: '{0:,.0f}'.format(value).replace(',', '.') for key, value in pop_dict.items()}
    print(pop_dict)