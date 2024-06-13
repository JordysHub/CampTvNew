import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # Execute spots collection script
    os.system("collect_spots.py")

    # Execute spots processing script
    os.system("process_spots.py")
    
    # Update all spots file
    os.system("update_spots_file.py")
    
    # Execute flights collection script
    os.system("create_flights.py")
    
    # Execute bereik collection script
    os.system("process_bereik.py")

if __name__ == "__main__":
    main()