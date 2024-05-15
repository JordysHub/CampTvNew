#!/bin/bash

# Set the source and destination directories
SOURCE_DIR_BEREIK="./data/raw/api/bereik"
SOURCE_DIR_SPOTS="./data/raw/api/spots"
SOURCE_DIR_FLIGHTS="./data/interim/flights"
DEST_DIR="./data/backup"

# Create a backup directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Generate a timestamp for the backup folders
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Copy each source directory to the backup directory
cp -r "$SOURCE_DIR_BEREIK" "$DEST_DIR/bereik_backup_$TIMESTAMP"
cp -r "$SOURCE_DIR_SPOTS" "$DEST_DIR/spots_backup_$TIMESTAMP"
cp -r "$SOURCE_DIR_FLIGHTS" "$DEST_DIR/flights_backup_$TIMESTAMP"

# Run your main script to fetch new data
python src/scripts/get_spots_raw.py
python src/scripts/process_spots.py
python src/scripts/process_flights.py
python src/scripts/get_bereik_raw.py
python src/scripts/process_bereik.py