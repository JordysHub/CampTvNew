from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import logging

load_dotenv()
logger = logging.getLogger("connection_utils.py")

def create_sql_alchemy_engine():
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
