import camp_tv_new.src.utils.connection_utils as con_utils
from camp_tv_new.src.utils.logger import setup_logger, timer_func

import pandas as pd
from sqlalchemy import delete, text


logger = setup_logger()
def dump_to_sql(
    df,
    table_name,
    schema = 'dbo',
    if_exists = 'append',
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
    # confirmation = input(
    #     "Are you sure you want to execute this script and dump the data? (yes/no): "
    # )

    # # Check user's response
    # if confirmation.lower() == "yes":
    try:
        engine = con_utils.create_sql_alchemy_engine()
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
            method=method,
            chunksize=chunksize,
        )

    except Exception as e:
        logger.error(f"An error occurred while dumping the data to the database: {str(e)}")

def check_existing_primary_keys(df: pd.DataFrame, table_name: str,  column_name: str, schema: str = 'dbo') -> pd.DataFrame:
        # Create a SQLAlchemy engine
        engine = con_utils.create_sql_alchemy_engine()

        # Load existing primary keys from the database
        existing_keys_query = f"SELECT DISTINCT {column_name} FROM [{schema}].[{table_name}];"
        existing_keys = pd.read_sql(existing_keys_query, engine)[column_name].tolist()

        # Filter out rows with existing primary keys
        df_to_insert = df[~df[column_name].isin(existing_keys)]

        return df_to_insert

def get_all_dates_from_db():
    query = """
    SELECT DISTINCT [date]
    FROM [dbo].[tv.spots]
    """
    engine = con_utils.create_sql_alchemy_engine()
    # Execute the query and load the data into a DataFrame
    df_distinct_dates = pd.read_sql_query(query, engine)

    # If the date column is not in datetime format, convert it
    df_distinct_dates['date'] = pd.to_datetime(df_distinct_dates['date'])

    # Sort the dates if needed
    df_distinct_dates = df_distinct_dates.sort_values(by='date')
    list_of_dates = df_distinct_dates['date'].tolist()

    return list_of_dates

def query_to_df(query):
    engine = con_utils.create_sql_alchemy_engine()
    df_query = pd.read_sql_query(query, engine)

    return df_query

def delete_flights(list_of_flights, table_name, target_group = None):
    try:
        # Connect to the database
        engine = con_utils.create_sql_alchemy_engine()
        # Convert list_of_flights to a tuple for use in the SQL query
        list_of_flights = tuple(list_of_flights)

        # Construct the SQL DELETE statement
        sql_delete = f"""
        DELETE FROM [dbo].{table_name}
        WHERE flight_id IN {list_of_flights}
        """

        if target_group is not None:
            sql_delete += f" AND target_group = '{target_group}'"

        with engine.connect() as connection:
            # Begin a transaction
            with connection.begin() as transaction:
                try:
                    # Execute the DELETE statement
                    connection.execute(text(sql_delete))
                    # Commit the transaction
                    transaction.commit()
                except Exception as e:
                    # Rollback the transaction in case of error
                    transaction.rollback()
                    logger.error(f"Error deleting flights: {e}")
                    raise

        logger.info(f"{len(list_of_flights)} flights deleted successfully.")

    except Exception as e:
        logger.error(f"Error deleting flights: {e}")