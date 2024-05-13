import utils.connection_utils as con_utils
from utils.connection_utils import timer_func


@timer_func
def dump_to_sql(
    start_date,
    end_date,
    df,
    table_name,
    schema,
    if_exists="append",
    index=False,
    method="multi",
    chunksize=50,
):
    """
    A function to dump a pandas DataFrame to a SQL database using SQLAlchemy.

    Parameters:
        df (DataFrame): The pandas DataFrame to be dumped.
        table_name (str): The name of the table in the database.
        schema (str): The schema to be used in the database.
        if_exists (str, optional): Action to take if the table already exists.
        index (bool, optional): Write DataFrame index as a column.
        method (str, optional): The method to be used to insert data.
        chunksize (int, optional): The number of rows to write at a time.

    Returns:
        None
    """
    # Ask for user confirmation
    confirmation = input(
        "Are you sure you want to execute this script and dump the data? (yes/no): "
    )

    # Check user's response
    if confirmation.lower() == "yes":
        print(
            f"Processing {table_name} data, in the period {start_date} to {end_date}, and dumping it into the [{table_name}][{schema}] database."
        )
        print("Script execution started...")
        engine = con_utils.create_sql_alchemy_engine()
        print("Info: Starting dump")
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
            method=method,
            chunksize=chunksize,
        )
        print("Info: Dump finished")
        print("Script executed successfully.")
    else:
        print("Script execution aborted.")
