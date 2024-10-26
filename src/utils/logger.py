import logging
from time import time
from datetime import datetime
import os
import pandas as pd


# Setup logger function
def setup_logger(script_name, log_dir='logs', console_logging=False):
    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Define the path for the script-specific log file
    log_file_path = os.path.join(log_dir, f"{script_name}.log")

    # Create a logger for the script
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)  # Start with DEBUG level

    # Avoid duplicate handlers if the logger is called multiple times
    if not logger.handlers:
        # File handler for logging INFO level and above
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%d-%m-%Y %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler for DEBUG level and above (optional)
        if console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # Configure 'requests' and 'urllib3' loggers to avoid excessive logging
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger

# Define custom formatter for terminal output

class TerminalFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "%(asctime)s - %(levelname)s - %(message)s",
        logging.INFO: "\033[92m%(asctime)s - %(levelname)s - %(message)s\033[0m",
        logging.WARNING: "\033[93m%(asctime)s - %(levelname)s - %(message)s\033[0m",
        logging.ERROR: "\033[91m%(asctime)s - %(levelname)s - %(message)s\033[0m",
        logging.CRITICAL: "\033[91m%(asctime)s - %(levelname)s - %(message)s\033[0m",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "[DEBUG] [%(name)s] - %(asctime)s - %(message)s",
        logging.INFO: "[INFO] [%(name)s] - %(asctime)s - %(message)s",
        logging.WARNING: "[WARNING] %(asctime)s - %(message)s",
        logging.ERROR: "[ERROR] %(asctime)s - %(message)s",
        logging.CRITICAL: "[CRITICAL] %(asctime)s - %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def timer_func(func):
    # Decorator function to measure the execution time of the input function.
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='pipeline.log',
                    filemode='w')

    logger = logging.getLogger(__name__)

    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        logger.info(f"TIME - Function {func.__name__!r} executed in {(t2 - t1):.4f}s")
        return result

    return wrap_func


def log_warning_to_excel(
    flight_id,
    advertiser,
    product,
    start_date,
    end_date,
    file_path="data/interim/warnings.xlsx",
):
    # Create a dictionary for the new row
    new_row = {
        "flight_id": flight_id,
        "advertiser": advertiser,
        "product": product,
        "start_date": start_date,
        "end_date": end_date,
    }

    new_df = pd.DataFrame([new_row])

    # Check if the file exists
    if os.path.exists(file_path):
        # Load existing data
        df_existing = pd.read_excel(file_path)

        # Check if the flight_id already exists
        if not df_existing[df_existing["flight_id"] == flight_id].empty:
            return

        # Append new row to the existing dataframe
        df_existing = pd.concat([df_existing, new_df], ignore_index=True)

    else:
        # If file does not exist, use the new dataframe as the dataframe to be saved
        df_existing = new_df

    # Save the dataframe to the Excel file
    df_existing.to_excel(file_path, index=False)
