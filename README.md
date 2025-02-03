# **Project Description**
The project aims to forecast the 1+ reach for Ster campaigns with a ML model by leveraging key features such as GRPs, time-based factors, and (sporting) events. It automates the entire process, gathering all the necessary data to train the machine learning model used for these predictions.

# **Project Overview**
```
.
└── CAMP_TV_NEW/
    ├── data/
    │   └── interim/
    │       └── warnings.xlsx            # Some flights mismatch in Edge, causing the API to return an error. I store and remove these flights to prevent issues in the future.
    ├── models/
    │   ├── model_results.json           # stores all the training results
    │   ├── model_summary.ipynb          # creates a readable cell from the model results
    │   ├── trainer_class.ipynb          # contains the classes to train the models with
    │   ├── 
    ├── notebooks/
    │   └── calculate_corrections.ipynb   # used for correcting the old models
    │   ├── clustering.ipynb              # used for making clustering predictions to see if models can predict multiple target groups
    │   ├── data_overview.ipynb           # gives and overview of what data is stored in the database per target group
    │   ├── update_alcolhol.ipynb         # due to some mistake, the feature 'alcohol' didnt work. This corrects the data in the database
    ├── src/
    │   ├── scripts/
    │   │   ├── calculate_pop.py           # Caluclates and updates the target group population in the database
    │   │   ├── collect_bereik_ster.py     # Collects reach per target group from edge for every created (mock)flight
    │   │   ├── collect_spots.py           # Collects all the (ster)spots per day
    │   │   └── create_flights.py          # Create (mock)flights from the collected spots
    │   ├── tests/
    │   │   └── test_flights.py            # Pytests for data in database
    │   └── utils                          # all the utility functions used in the main scripts/
    │       ├── api_utils.py
    │       ├── bereik_utils.py
    │       ├── connection_utils.py
    │       ├── database_utils.py
    │       ├── dictionaries.py
    │       ├── flight_utils.py
    │       ├── logger.py
    │       ├── prediction_utils.py
    │       ├── process_spots.py
    │       ├── query_dict.py
    │       └── test_api.py
    ├── .env
    ├── .gitignore
    ├── format_project.py               # linting and formatting project code
    ├── make.bat
    ├── pipeline.log
    ├── pipeline.py                # Runs the whole pipeline (all the scripts + the pytests). Can run this every other week to collect new spots/flights etc.
    ├── README.md
    └── requirements.txt
```
# **Installation Instructions**:
- git pull request from `https://dev.azure.com/ster-nl/DataScience/_git/CampTvNew`
- create virtual environment with `py -3.11 -m venv .venv` or within VScode
- activate virtual environment with `.venv\Scripts\activate.ps1`
- install requirements with `pip install -r requirements.txt`

# **Usage**:
- set terminal path in main folder and run pipeline with `pyton pipeline.py` or any script (for example `python src/scripts/collect_spots.py`)

See wiki for running all the scripts and their possible arguments

# **Requirements/Dependencies:**
- colorlog
- numpy
- pandas
- setuptools==69.5.1
- SQLAlchemy==2.0.31
- tqdm==4.66.2
- python-dotenv
- requests
- openpyxl==3.1.5
- pyodbc
- pytest

# **Contributing:**

# Author:

# **Known Issues/Bugs:**

# Changelog:
