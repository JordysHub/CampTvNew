from dotenv import load_dotenv
import pandas as pd
import os

from camp_tv_new.src.scripts.collect_spots import get_spots
from src.scripts.update_spots_file import update_all_spots_file
from camp_tv_new.src.scripts.create_flights import create_flights_from_spots
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger()

def main():
    raw_spots_folder = os.getenv("raw_spots_folder")
    processed_spots_folder = os.getenv("processed_spots_folder")
    all_spots_path = os.getenv("all_spots_path")
    all_flights_path = os.getenv("all_flights_path")
    
    # Collect raw spots from api
    get_spots(raw_spots_folder, processed_spots_folder)
    # Update all spots
    update_all_spots_file(all_spots_path, processed_spots_folder)
    df_spots = pd.read_excel(all_spots_path)
    logger.info(f"Updated all_spots file. First and last date in spots file: {df_spots['date'].min().date()} - {df_spots['date'].max().date()}")

    # Create flights from all spots
    create_flights_from_spots(df_spots, all_flights_path)

if __name__ == "__main__":
    main()