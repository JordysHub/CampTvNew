from datetime import datetime
import pandas as pd
import os
import camp_tv_new.src.utils.preprocess_spots as prep_spots
import camp_tv_new.src.utils.flights_utils as fu
import camp_tv_new.src.utils.date_utils as date_utils

from dotenv import load_dotenv
from utils.logger import setup_logger, timer_func
import json

load_dotenv()
logger = setup_logger()

def process_raw_spots(raw_spots_folder, processed_spots_folder):
    existing_raw_spots_dates = date_utils.get_existing_dates_in_folder(raw_spots_folder)
    existing_processed_spots_dates = date_utils.get_existing_dates_in_folder(processed_spots_folder)

    # Determine missing dates
    missing_dates = [date for date in existing_raw_spots_dates if date not in existing_processed_spots_dates and date.month != 8]

    if missing_dates:
        logger.info(f'Fetching spots from {min(missing_dates).date()} to {max(missing_dates).date()}')
        for datum in missing_dates:
            raw_file_path = os.path.join(raw_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
            processed_file_path = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
            processed_root_folder = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/'))

            if not os.path.exists(processed_root_folder):
                os.makedirs(processed_root_folder)

            df = pd.read_excel(raw_file_path, parse_dates=['date'])
            df['date'] = pd.to_datetime(df['date']).dt.date

            # convert strings in GRP columns to lists (as returned by the API)
            for col in df.columns[5:]:
                df[col] = df[col].apply(eval)

            df = prep_spots.tv_clean_df(df)
            df_ids = prep_spots.determine_ids(df)
            df = prep_spots.add_dayparts(df)

            df = df.merge(df_ids, on=["advertiser", "product"], how="left").sort_values(by=["date", "advertiser"])
            df.to_excel(processed_file_path, index=False)
    else:
        logger.debug('Processed all daily spots')

def update_all_spots_file(all_spots_path, processed_spots_folder):
    all_spots_file_dates = date_utils.get_existing_dates_in_all_spots(all_spots_path)
    existing_processed_spots_dates = date_utils.get_existing_dates_in_folder(processed_spots_folder)
    
    # Get all dates from the start of the existing spots dates to the latest processed date
    if all_spots_file_dates:
        missing_dates = [date for date in existing_processed_spots_dates if date not in all_spots_file_dates and date.month != 8]
    else:
        missing_dates = existing_processed_spots_dates

    if missing_dates:
        logger.info(f'Processing spots from {min(missing_dates).date()} to {max(missing_dates).date()}')
        dfs = []
        filtered_dict = {}
        
        for datum in missing_dates:
            processed_file_path = os.path.join(processed_spots_folder, datum.strftime('%Y/%m/%d') + '.xlsx')
            df = pd.read_excel(processed_file_path)[["advertiser", "product", "date", "hour"]]
            dfs.append(df)

        new_df = pd.concat(dfs)
        new_df['hour'] = new_df['hour'].str.replace('24:00:00', '00:00:00').str.replace('25:00:00', '01:00:00')
        new_df['hour'] = pd.to_datetime(new_df['hour'], format='%H:%M:%S')
        
        # Count spots per day for each advertiser
        spot_counts = new_df.groupby(['advertiser', 'product', 'date']).size().reset_index(name='spot_count')
        df_spots = new_df.merge(spot_counts, on=['advertiser', 'product', 'date'])
        df_spots = df_spots[['advertiser', 'product', 'date', 'spot_count']].drop_duplicates()
        
        # Determine alcohol and kansspelen
        grouped_df = new_df.groupby(['advertiser', 'product'])
        filtered_groups = grouped_df.filter(lambda x: all((x['hour'].dt.hour >= 21) | (x['hour'].dt.hour <= 2)))
        filtered_pairs = set(filtered_groups[['advertiser', 'product']].apply(tuple, axis=1))

        for advertiser, product in filtered_pairs:
            if advertiser not in filtered_dict:
                filtered_dict[advertiser] = set()
            filtered_dict[advertiser].add(product)
            
        filtered_dict_serializable = {k: list(v) for k, v in filtered_dict.items()}
        logger.info(f'Filtered dictionary: {json.dumps(filtered_dict_serializable, indent=2)}')
                
        try:
            all_spots_df = pd.read_excel(all_spots_path, parse_dates=["date"])
            all_spots_df = pd.concat([all_spots_df, df_spots])
            all_spots_df.to_excel(all_spots_path, index=False)
        except UnboundLocalError: 
            df_spots.to_excel(all_spots_path, index=False)           
            
    else: 
        logger.debug('Fetched and concatenated all spots')
        
@timer_func
def create_flights_from_spots(df_spots: pd.DataFrame, all_flights_path: str):
    """
    Create flights from spots dataframe.
    
    Args:
        df_spots (pd.DataFrame): Spots dataframe.
        all_flights_path (str): Path to the output flights excel file.
    """
    # Segment campaigns by new start date
    df_flights = fu.flights_segment_campaigns_by_new_start(df_spots)
    # Determine start and end campaign dates
    df_flights = fu.get_start_end_campaign_date(df_flights)
    # Split campaigns that are longer than two months
    df_flights = fu.split_campaigns(df_flights)
    
    # Prepare and make mock flights
    df_flights['mock_campaign'] = False
    mock_campaigns_df = fu.create_mock_campaigns(df_flights)

    # Change date format to DDMMYY (easier to use for api)
    df_flights['start_date'] = pd.to_datetime(df_flights['start_date']).dt.strftime("%d%m%y")
    df_flights['end_date'] = pd.to_datetime(df_flights['end_date']).dt.strftime("%d%m%y")
    mock_campaigns_df['start_date'] = pd.to_datetime(mock_campaigns_df['start_date']).dt.strftime("%d%m%y")
    mock_campaigns_df['end_date'] = pd.to_datetime(mock_campaigns_df['end_date']).dt.strftime("%d%m%y")
    
    # Create unique flight_id
    df_flights['flight_id'] = df_flights.apply(fu.generate_uuid_from_columns, axis=1)
    mock_campaigns_df['flight_id'] = mock_campaigns_df.apply(fu.generate_uuid_from_columns, axis=1)
    
    df_flights.sort_values(['advertiser', 'product', 'start_date', 'end_date'], inplace=True)
    mock_campaigns_df.sort_values(['advertiser', 'product', 'start_date', 'end_date'], inplace=True)
    
    df_flights.to_excel("./data/interim/flights/all_flights.xlsx", index=False)
    mock_campaigns_df.to_excel("./data/interim/flights/mock_campaigns_df.xlsx", index=False)

def main():

    # Define folder paths
    raw_spots_folder = os.getenv("raw_spots_folder")
    processed_spots_folder = os.getenv("processed_spots_folder")
    all_spots_path = os.getenv("all_spots_path")
    all_flights_path = os.getenv("all_flights_path")
    
    # Process raw spots
    process_raw_spots(raw_spots_folder, processed_spots_folder)
    # Update all spots
    update_all_spots_file(all_spots_path, processed_spots_folder)
    df_spots = pd.read_excel(all_spots_path)
    logger.info(f"Updated all_spots file. First and last date in spots file: {df_spots['date'].min().date()} - {df_spots['date'].max().date()}")

    # Create flights from all spots
    create_flights_from_spots(df_spots, all_flights_path)

if __name__ == "__main__":
    main()