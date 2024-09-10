import os
import logging
from dotenv import load_dotenv
from src.utils.logger import timer_func

load_dotenv()

# Set up logging to a file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='pipeline.log',
                    filemode='w')

logger = logging.getLogger(__name__)

@timer_func
def run_script(script_name):
    """
    Function to execute a Python script and log its execution status.

    Parameters:
        script_name (str): The name of the script to execute.

    Returns:
        int: The exit code of the script execution (0 for success, non-zero for failure).
    """
    logger.info(f"Executing {script_name}...")
    result = os.system(f"python {script_name}")

    if result == 0:
        logger.info(f"{script_name} completed successfully.")
    else:
        logger.error(f"{script_name} failed with exit code {result}")

    return result

def main():
    try:
        run_script("src/scripts/collect_spots.py")
        run_script("src/scripts/create_flights.py")
        run_script("src/scripts/collect_bereik_ster.py")
        run_script("src/scripts/calculate_pop.py")

        # Run pytest at the end
        run_script("-m pytest")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()