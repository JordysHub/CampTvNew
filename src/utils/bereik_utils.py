import camp_tv_new.src.utils.dictionaries as dict
import camp_tv_new.src.utils.api_utils as api_utils
from camp_tv_new.src.utils.logger import setup_logger

from icecream import ic
import pandas as pd
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
        logger.warning(f"Skipping row due to df being empty {index}")
        return pd.DataFrame()

    df = df.rename(columns={0: 'advertiser', 1: 'product', 2: 'daypart'})
    df.insert(0, "flight_id", str(flight_id))
    df.insert(1, "start_date", str(start_date))
    df.insert(2, "end_date", str(end_date))

    return df

def clean_up_bereik_tv(df):
    # Create columns for dataframe based on input from cells
    # Find starting index from where R&F starts, migh be different because of the amount of exploitanten

    bereik_start_index = [x[1] for x in df.values[0]].index("1+ (%)")
    api_grp_list = [f'{x[2].lower().replace(" ", "")}_grp' for x in df.values[0][3:bereik_start_index]]
    api_bereik_list = [f'{x[2].lower().replace(" ", "")}{dict.bereik_dict_tv[x[1]]}' for x in df.values[0][bereik_start_index:]]

    df.columns = ["advertiser", "product", "daypart"] + api_grp_list + api_bereik_list
    df.iloc[:, 3:] = df.iloc[:, 3:].apply(lambda x: x.apply(lambda x: float(str(x[-1]).replace(",", ""))), axis=1)

    # Create empty original dataframe
    grp_columns = [f"{x}_grp" for x in dict.expl_list_tv]
    bereik_list = ["_1bereik", "_3bereik", "_6bereik", "_3_5bereik"]
    bereik_type_columns = [str(x) + str(y) for x in dict.expl_list_tv for y in bereik_list]
    empty_df = pd.DataFrame(columns=["advertiser", "product", "daypart"] + grp_columns + bereik_type_columns)

    common_columns = list(set(empty_df.columns) & set(df.columns))
    merged_df = pd.merge(empty_df, df, how='outer', on=common_columns)
    merged_df.to_excel("./data/processed/bereik/testtt.xlsx")

    # Fill missing values (NaNs) with zeroes
    merged_df.fillna(0, inplace=True)

    return merged_df


def clean_up_bereik_radio(df):

    bereik_str_map_dict = dict.bereik_dict_radio

    # Create columns for dataframe based on input from cells
    # Find starting index from where R&F starts, migh be different because of the amount of exploitanten
    bereik_start_index = [x[1] for x in df.values[0]].index('1+ (%)')
    count_start_index = [x[1] for x in df.values[0]].index('Count')

    spots_list = [f'{x[2].lower().replace(" ", "")}_spots' for x in df.values[0][3:count_start_index]]
    grp_list = [f'{x[2].lower().replace(" ", "")}_grp' for x in df.values[0][count_start_index:bereik_start_index]]
    bereik_list = [f'{x[2].lower().replace(" ", "")}{bereik_str_map_dict[x[1]]}' for x in df.values[0][bereik_start_index:]]

    df.columns = ['advertiser', 'product', 'daypart'] + grp_list + spots_list + bereik_list

    # Change the bereik data from European notation to American
    df.iloc[:, 3:] = df.iloc[:, 3:].apply(
        lambda x: x.apply(lambda x: float(str(x[-1]).replace('-', '0,0').replace('.', '').replace(',', '.'))), axis=1)

    # Create all ster_1, ster_3 ... oms, etc. type of empty columns
    expl_list = ['nporadio1', 'nporadio2', 'npo3fm', 'npoklassiek', 'nporadio5', 'sterradiozenders', 'radio10', 'radio538', 'veronica', 'skyradio', 'slam', '100%nl', 'OMS', 'Qmusic', 'BNRNieuws', 'Total']
    spots_columns = [f'{x}_spots' for x in expl_list] 
    grp_columns = [f'{x}_grp' for x in expl_list]  
    bereik_type_list = [f'{x}bereik' for x in range(1, 12)]
    bereik_type_columns = [x for x in [[f'{expl}_{bereik_type}' for bereik_type in bereik_type_list] for expl in
                                       expl_list] for x in x]

    # # Create an empty DataFrame with the desired columns
    empty_df = pd.DataFrame(columns=['advertiser', 'product', 'daypart'] + grp_columns + spots_columns + bereik_type_columns)

    # # Concatenate the empty DataFrame and the original DataFrame while ignoring index
    df = pd.concat([empty_df, df], ignore_index=True).fillna(0)

    return df

"""
def create_grp_bereik_columns(df, medium):

    if medium == "tv":
        bereik_start_index = [x[1] for x in df.values[0]].index("1+ (%)")
        grp_list = [f'{x[2].lower().replace(" ", "")}_grp' for x in df.values[0][3:bereik_start_index]]
        bereik_list = [f'{x[2].lower().replace(" ", "")}{dict.bereik_dict_tv[x[1]]}' for x in df.values[0][bereik_start_index:]]
        for old, new in dict.bereik_rename_dict_tv.items():
            grp_list = [x.replace(old, new) for x in grp_list]
        df.columns = ["advertiser", "product", "daypart"] + grp_list + bereik_list

    if medium == "radio":
        bereik_start_index = [x[1] for x in df.values[0]].index("1+ (%)")
        count_start_index = [x[1] for x in df.values[0]].index("Count")
        grp_list = [f'{x[2].lower().replace(" ", "")}_grp' for x in df.values[0][count_start_index:bereik_start_index]]
        bereik_list = [f'{x[2].lower().replace(" ", "")}{dict.bereik_dict_radio[x[1]]}' for x in df.values[0][bereik_start_index:]]
        spots_list = [f'{x[2].lower().replace(" ", "")}_spots' for x in df.values[0][3:count_start_index]]
        df.columns = ["advertiser", "product", "daypart"] + grp_list + spots_list + bereik_list

    return df

def change_notation_bereik(df, medium):
    if medium == "tv":
        df.iloc[:, 3:] = df.iloc[:, 3:].apply(lambda x: x.apply(lambda x: float(str(x[-1]).replace(",", ""))), axis=1)
    if medium == "radio":
        df.iloc[:, 3:] = df.iloc[:, 3:].apply(
            lambda x: x.apply(lambda x: float(str(x[-1]).replace("-", "0,0").replace(".", "").replace(",", "."))), axis=1)

    return df

def create_columns_bereik(df, medium):

    if medium == "tv":
        # Create all ster_1, ster_3 ... talpa_6, talpa_3-5, etc. type of empty columns
        grp_columns = [f"{x}_grp" for x in dict.grp_expl_list_tv]
        bereik_type_list = ["1bereik", "3bereik", "6bereik", "3_5bereik"]
        bereik_type_columns = [
            x for x in [[f"{expl}_{bereik_type}" for bereik_type in bereik_type_list] for expl in dict.brk_expl_list_tv]
            for x in x]

        # Remove bereik columns for channels for competitors, only predicting total of competitor
        brk_drop_cols = [col for col in df.columns if (col.endswith("bereik")) and (col not in bereik_type_columns)]
        df = df.drop(brk_drop_cols, axis=1)

        columns = ["advertiser", "product", "daypart"] + grp_columns + bereik_type_columns
        df = pd.concat([pd.DataFrame(columns=columns), df], ignore_index=True).fillna(0.0)  # creates future warning

    if medium == 'radio':
        # Create all ster_1, ster_3 ... oms, etc. type of empty columns
        spots_columns = [f"{x}_spots" for x in dict.brk_expl_list_radio]
        grp_columns = [f"{x}_grp" for x in dict.brk_expl_list_radio]
        bereik_type_list = [f"{x}bereik" for x in range(1, 11)]
        bereik_type_columns = [x for x in [[f"{expl}_{bereik_type}" for bereik_type in bereik_type_list] for expl in dict.brk_expl_list_radio] for x in x]

        # # Create an empty DataFrame with the desired columns
        columns = pd.DataFrame(columns=["advertiser", "product", "daypart"] + grp_columns + spots_columns + bereik_type_columns)
        df = pd.concat([pd.DataFrame(columns=columns), df], ignore_index=True).fillna(0)  # creates future warnings

    return df

"""
