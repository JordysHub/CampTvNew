import logging
from time import time
import os

class TerminalFormatter(logging.Formatter):
    # ANSI color codes
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    FORMATS = {
        logging.DEBUG: WHITE + "%(asctime)s - %(levelname)s - %(message)s" + RESET,
        logging.INFO: GREEN + "%(asctime)s - %(levelname)s - %(message)s" + RESET,
        # Yellow for warning
        logging.WARNING: "\033[93m%(asctime)s - %(levelname)s - %(message)s\033[0m",
        logging.ERROR: RED + "%(asctime)s - %(levelname)s - %(message)s" + RESET,
        logging.CRITICAL: RED + "%(asctime)s - %(levelname)s - %(message)s" + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(
            record.levelno, self.WHITE + "%(asctime)s - %(levelname)s - %(message)s" + self.RESET)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

def setup_logger():
    logger = logging.getLogger("MyLogger")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Prevent messages from being propagated to the root logger

        # Console handler with TerminalFormatter for colored output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(TerminalFormatter())
        logger.addHandler(console_handler)

        # File handler to append logs to a single file
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists

        # Use a single filename for all logs
        log_filename = os.path.join(log_dir, "daily_log.log")
        file_handler = logging.FileHandler(log_filename, mode="a")
        file_handler.setLevel(logging.DEBUG)

        # Set a simpler format for the file logs (no colors needed)
        file_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def timer_func(func):
    # Decorator function to measure the execution time of the input function.
    logger = logging.getLogger("MyLogger")

    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        logger.info(
            f"TIME - Function {func.__name__!r} executed in {(t2 - t1):.4f}s")
        print(
            f"TIME - Function {func.__name__!r} executed in {(t2 - t1):.4f}s")
        return result

    return wrap_func
