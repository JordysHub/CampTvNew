import logging
from time import time
from datetime import datetime
import os
import pandas as pd

def setup_logger(base_log_path="src/scripts/logs/", console_logging=True):
    # Ensure the log directory exists
    if not os.path.exists(base_log_path):
        os.makedirs(base_log_path)

    # Create logger instance
    logger = logging.getLogger()

    # Check if logger already has handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Configure the root logger
    logger.setLevel(logging.DEBUG)

    # Configure the logging level for the requests library
    requests_logger = logging.getLogger("requests")
    requests_logger.setLevel(logging.WARNING)

    # Configure the logging level for urllib3, which is used by requests
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.WARNING)

    # Create log file with date-based name
    current_time = datetime.now()
    log_file = f"{current_time.strftime('%d-%m')}_daily_log_.log"
    log_file_path = os.path.join(base_log_path, log_file)

    # File handler for logging INFO level and higher
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_formatter = FileFormatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler for logging DEBUG level and higher
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = TerminalFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger

# Define custom formatter for terminal output
class TerminalFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '%(asctime)s - %(levelname)s - %(message)s',
        logging.INFO: '\033[92m%(asctime)s - %(levelname)s - %(message)s\033[0m',
        logging.WARNING: '\033[93m%(asctime)s - %(levelname)s - %(message)s\033[0m',
        logging.ERROR: '\033[91m%(asctime)s - %(levelname)s - %(message)s\033[0m',
        logging.CRITICAL: '\033[91m%(asctime)s - %(levelname)s - %(message)s\033[0m'
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '[DEBUG] [%(name)s] - %(asctime)s - %(message)s',
        logging.INFO: '[INFO] [%(name)s] - %(asctime)s - %(message)s',
        logging.WARNING: '[WARNING] %(asctime)s - %(message)s',
        logging.ERROR: '[ERROR] %(asctime)s - %(message)s',
        logging.CRITICAL: '[CRITICAL] %(asctime)s - %(message)s'
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


def timer_func(func):
    # Decorator function to measure the execution time of the input function.
    logger = setup_logger()

    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        logger.info(f"TIME - Function {func.__name__!r} executed in {(t2 - t1):.4f}s")
        return result

    return wrap_func

def log_warning_to_excel(flight_id, advertiser, product, start_date, end_date, file_path='data/interim/warnings.xlsx'):
    # Create a dictionary for the new row
    new_row = {
        'flight_id': flight_id,
        'advertiser': advertiser,
        'product': product,
        'start_date': start_date,
        'end_date': end_date
    }

    new_df = pd.DataFrame([new_row])

    # Check if the file exists
    if os.path.exists(file_path):
        # Load existing data
        df_existing = pd.read_excel(file_path)

        # Check if the flight_id already exists
        if not df_existing[df_existing['flight_id'] == flight_id].empty:
            return

        # Append new row to the existing dataframe
        df_existing = pd.concat([df_existing, new_df], ignore_index=True)

    else:
        # If file does not exist, use the new dataframe as the dataframe to be saved
        df_existing = new_df

    # Save the dataframe to the Excel file
    df_existing.to_excel(file_path, index=False)
