@timer_func
def process_file(file_path, parent_folder):
    """
    Process a single file by updating the flight_id for each row of data.
    Args:
        file_path (str): Path to the file.
    """
    bereik_processed_folder = os.getenv("bereik_processed_folder")
    # Read the file and process each row
    df = pd.read_excel(file_path, dtype={'start_date': str, 'end_date': str})
    processed_rows = [bereik_utils.process_row(row) for _, row in df.iterrows()]
    processed_df = pd.DataFrame(processed_rows).fillna(0)
    # change column order
    processed_df = bereik_utils.change_column_order(processed_df)
    # Write the updated DataFrame back to the Excel file
    output_file_path = os.path.join(bereik_processed_folder, parent_folder, os.path.basename(file_path))
    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    # Save the DataFrame to Excel
    processed_df.to_excel(output_file_path, index=False)

def process_directory(directory_path):
    """
    Process all files in a directory and its subdirectories.
    Args:
        directory_path (str): Path to the directory.
    """
    total_files = sum(len(files) for _, _, files in os.walk(directory_path))
    with tqdm(total=total_files, desc="Processing Files") as pbar_files:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.xlsx'):
                    file_path = os.path.join(root, file)
                    parent_folder = os.path.basename(os.path.dirname(file_path))
                    process_file(file_path, parent_folder)
                    pbar_files.update(1)  # Update progress bar for each file processed

    # logger.info("Raw bereik fetched for all flights")
    # logger.info("Process raw bereik...")

    # raw_bereik_folder = os.getenv("raw_bereik_folder") 
    # process_directory(raw_bereik_folder)

    # logger.info("Bereik processed for all target groups")