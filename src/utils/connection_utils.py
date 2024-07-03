
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

def create_sql_alchemy_engine():
    from sqlalchemy import create_engine
    from urllib.parse import quote_plus
    """
    Creates and returns a SQLAlchemy engine for connecting to a SQL Server database.
    """
    quoted = quote_plus(
        "Driver={ODBC+Driver+17+for+SQL+Server};"
        "Server=tcp:stercampsql.database.windows.net;"
        "Database=SterCampNew;"
        "uid=stercampadmin;"
        f"pwd={os.getenv('SQLDB')}"
    )
    alchemy_con = "mssql+pyodbc:///?odbc_connect={}".format(quoted)
    engine = create_engine(alchemy_con)

    return engine

def execute_query_to_df(query):
    engine = create_sql_alchemy_engine()
    SQL_Query = pd.read_sql_query(query, engine)
    df = pd.DataFrame(SQL_Query)

    return df
