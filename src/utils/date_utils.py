import pandas as pd
import os

# def get_existing_dates_in_folder(folder_path, date_format='%Y\\%m\\%d.xlsx'):
#     existing_dates = []
#     for root, _, files in os.walk(folder_path):
#         for file in files:
#             if file.endswith('.xlsx'):
#                 relative_path = os.path.relpath(os.path.join(root, file), folder_path)
#                 try:
#                     date = pd.to_datetime(relative_path, format=date_format)
#                     existing_dates.append(date)
#                 except ValueError:
#                     continue

#     return existing_dates

# def get_existing_dates_in_all_spots(all_spots_path):
#     try:
#         all_spots_df = pd.read_excel(all_spots_path, parse_dates=["date"])
#         existing_dates = all_spots_df['date'].unique()
#         return pd.to_datetime(existing_dates).tolist()
#     except FileNotFoundError:
#         return []