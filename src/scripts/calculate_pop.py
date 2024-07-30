# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# region imports and warnings
import camp_tv_new.src.utils.api_utils as api_utils
import camp_tv_new.src.utils.dictionaries as mydict
from camp_tv_new.src.utils.logger import setup_logger
import camp_tv_new.src.utils.database_utils as db_utils

from dotenv import load_dotenv
import pandas as pd

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

    return int(population)

def fetch_and_process_data(target_groups, token):
    pop_dict = {}

    for tg in target_groups:
        try:
            df = api_utils.call_pop_report_tv(tg, token)
            pop_dict[tg] = calculate_pop(df)
        except Exception as e:
            print(f"Error processing target group {tg}: {e}")

    return pop_dict

def main():
    target_groups = [mydict.rename_column_for_api.get(tg, tg) for tg in mydict.target_groups]
    token = api_utils.get_api_token()

    pop_dict = fetch_and_process_data(target_groups, token)
    df_pop = (pd.DataFrame.from_dict(pop_dict, orient='index', columns=['population'])
          .reset_index()
          .rename(columns={'index': 'target_group'})
          .assign(target_group=lambda x: x['target_group'].replace(mydict.rename_dict),
                  population=lambda x: x['population'].astype(int)))

    db_utils.dump_to_sql(df_pop, 'tv.population', if_exists='replace')

if __name__ == "__main__":
    main()