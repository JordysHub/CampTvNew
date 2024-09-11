# **Project Description**


# **Project Overview**
```
.
└── CAMP_TV_NEW/
    ├── data/
    │   └── interim/
    │       ├── all_spots_ster.xlsx      # contains all spots per hour, which makes calculation alcohol/kansspel easier
    │       └── warnings.xlsx            # Some flights mismatch in Edge, causing the API to return an error. I store and remove these flights to prevent issues in the future.
    ├── notebooks/
    │   ├── predictions                  # stores prediction files
    │   ├── visualizations/
    │   │   └── visualize.ipynb
    │   ├── clustering.ipynb
    │   ├── data_overview.ipynb           # gives and overview of what data is stored in the database per target group
    │   └── model_trainer_class.ipynb     # The notebook used for training the models
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
    ├── format_project.py
    ├── make.bat
    ├── pipeline.log
    ├── pipeline.py                # Runs the whole pipeline (all the scripts + the pytests). Can run this every other week to collect new spots/flights etc.
    ├── README.md
    └── requirements.txt
```
# **Installation Instructions**:

# **Usage**:

# **Requirements/Dependencies:**

# **Contributing:**

# Author:

# **Known Issues/Bugs:**

# Changelog:
