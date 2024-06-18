import logging
from time import time
from colorlog import ColoredFormatter
from datetime import datetime
import os

def setup_logger(base_log_path="logs/", console_logging=True):
    # Create logger instance
    logger = logging.getLogger()

    # Check if logger already has handlers
    if logger.hasHandlers():
        return logger  # Return the logger if handlers are already set up

    # Configure the root logger
    logger.setLevel(logging.DEBUG)

    # Configure the logging level for the requests library
    requests_logger = logging.getLogger("requests")
    requests_logger.setLevel(logging.WARNING)
    # Configure the logging level for urllib3, which is used by requests
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.WARNING)
    
    # Create log directory based on the current year and month
    current_time = datetime.now()
    year = current_time.strftime('%Y')
    month = current_time.strftime('%m')
    log_folder = os.path.join(base_log_path, year, month)
    os.makedirs(log_folder, exist_ok=True)

    # Create log file with date-based name
    log_file = f"{current_time.strftime('%d')}_daily_log_.log"
    log_file_path = os.path.join(log_folder, log_file)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(FileFormatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S'))  # Use custom file formatter
    logger.addHandler(file_handler)

    # Create console handler if specified
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(TerminalFormatter())
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



# {datetime.now().strftime('%m-%Y')}/