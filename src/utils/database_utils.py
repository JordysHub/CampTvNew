import src.utils.connection_utils as con_utils
from src.utils.logger import setup_logger, timer_func

import pandas as pd
from sqlalchemy import text


logger = setup_logger()

def dump_to_sql(
    df,
    table_name,
    schema = 'dbo',
    if_exists = 'append',
    index=False,
    method="multi",
    chunksize=10,
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

def query_to_df(query):
    engine = con_utils.create_sql_alchemy_engine()
    with engine.connect() as connection:
        df_query = pd.read_sql_query(query, connection)

    return df_query

def delete_flights(list_of_flights, table_name, target_groups = None):
    try:
        # Connect to the database
        engine = con_utils.create_sql_alchemy_engine()
        # Convert list_of_flights to a tuple for use in the SQL query
        list_of_flights = tuple(list_of_flights)

        # Convert target_groups to a format suitable for SQL IN clause
        if target_groups:
            target_groups_str = ', '.join(f"'{tg}'" for tg in target_groups)
            target_groups_condition = f"AND target_group IN ({target_groups_str})"
        else:
            target_groups_condition = ""

        # Construct the SQL DELETE statement
        sql_delete = f"""
        DELETE FROM [dbo].[{table_name}]
        WHERE flight_id IN {list_of_flights}
        {target_groups_condition}
        """

        with engine.connect() as connection:
            # Begin a transaction
            with connection.begin() as transaction:
                try:
                    # Execute the DELETE statement
                    result = connection.execute(text(sql_delete))
                    # Get the number of rows deleted
                    rows_deleted = result.rowcount
                    # Commit the transaction
                    transaction.commit()
                    # Log the number of rows deleted
                    logger.info(f"{rows_deleted} flights deleted successfully.")
                except Exception as e:
                    # Rollback the transaction in case of error
                    transaction.rollback()
                    logger.error(f"Error deleting flights: {e}")
                    raise

    except Exception as e:
        logger.error(f"Error during the deletion process: {e}")