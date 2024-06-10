import utils.connection_utils as conn_utils
import pandas as pd
from datetime import datetime, date, timedelta
import os
from camp_tv_new.src.utils import api_utils

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
    date_str = conn_utils.execute_query_to_df(query).iloc[0, 0]
    start_date = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)

    return start_date

def get_existing_dates_in_folder(folder_path, date_format='%Y\%m\%d.xlsx'):
    existing_dates = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.xlsx'):
                relative_path = os.path.relpath(os.path.join(root, file), folder_path)
                try:
                    date = pd.to_datetime(relative_path, format=date_format)
                    existing_dates.append(date)
                except ValueError:
                    continue
    return existing_dates

def fetch_latest_date(folder_path):
    return api_utils.get_last_known_date_offline(folder_path)[0]

def get_all_dates_in_range(start_date, end_date):
    return pd.date_range(start=start_date, end=end_date)

def get_existing_dates_in_all_spots(all_spots_path):
    try:
        all_spots_df = pd.read_excel(all_spots_path, parse_dates=["date"])
        existing_dates = all_spots_df['date'].unique()
        return pd.to_datetime(existing_dates).tolist()
    except FileNotFoundError:
        return []