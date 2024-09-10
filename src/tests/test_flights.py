import src.utils.database_utils as db_utils
import pytest
import pandas as pd

@pytest.fixture(scope="module", autouse=True)
def preprocess():
    # some flights have a mismatch in Edge. These flights are logged in warnings.xlsx and can be deleted from the db, before running the tests
    warnings_df = pd.read_excel('data/interim/warnings.xlsx')
    wrong_flights = warnings_df['flight_id'].to_list()
    flights = ', '.join(f"'{flight}'" for flight in wrong_flights)
    db_utils.delete_flights(wrong_flights, 'tv.flights_ster')
    db_utils.delete_flights(wrong_flights, 'tv.bereik_ster')
    print(f"{len(flights)} deleted...")

def test_no_flights_with_count_greater_than_3():
    #There can't be more than 3 of the same flight per target_group (3 dayparts) in the bereik table
    sql_query = """
    SELECT target_group, flight_id
    FROM [dbo].[tv.bereik_ster]
    GROUP BY target_group, flight_id
    HAVING COUNT(*) > 3;
    """
    result_df = db_utils.query_to_df(sql_query)
    # Assert that the DataFrame is empty
    assert result_df.empty, "Expected no flights with count greater than 3, but found some."

def test_no_flights_with_count_greater_than_1():
    # There can't be more than 1 same flight_id in the flights table
    sql_query = """
    SELECT flight_id, COUNT(*) as count
    FROM [dbo].[tv.flights_ster]
    GROUP BY flight_id
    HAVING COUNT(*) > 1;
    """
    result_df = db_utils.query_to_df(sql_query)
    # Assert that the DataFrame is empty
    assert result_df.empty, "Expected no flights with count greater than 1, but found some."

def test_flights_in_bereik_do_exist_in_flights_table():
    sql_query = '''
    SELECT COUNT(*) AS count_flight_ids_not_in_flights_table
    FROM [dbo].[tv.bereik_ster]
    WHERE flight_id NOT IN (SELECT flight_id FROM [dbo].[tv.flights_ster])'''
    result_df = db_utils.query_to_df(sql_query)
    count_not_in_flights = result_df.iloc[0]['count_flight_ids_not_in_flights_table']
    # Assert that the DataFrame is empty
    assert count_not_in_flights == 0, f"Found {count_not_in_flights} flights that do not exist in the flights table"

def test_all_flights_exist_in_bereik():
    sql_query = """
    SELECT f.flight_id
    FROM [dbo].[tv.flights_ster] f
    LEFT JOIN [dbo].[tv.bereik_ster] b ON f.flight_id = b.flight_id
    WHERE b.flight_id IS NULL;
    """
    result_df = db_utils.query_to_df(sql_query)
    # Assert that the DataFrame is empty
    assert result_df.empty, f"Found flights that do not exist in bereik table: {result_df['flight_id'].tolist()}"

def test_all_flights_exist_in_bereik_per_target_group():
    sql_query = """
    SELECT
    b.target_group,
    COUNT(f.flight_id) AS missing_flight_count
    FROM
        [dbo].[tv.flights_ster] f
    LEFT JOIN
        [dbo].[tv.bereik_ster] b
    ON
        f.flight_id = b.flight_id
    GROUP BY
        b.target_group
    HAVING
        COUNT(b.flight_id) < (SELECT COUNT(*) FROM [dbo].[tv.flights_ster]);
    """
    result_df = db_utils.query_to_df(sql_query)
    # Assert that the DataFrame is empty
    assert result_df.empty, f"Found flights that do not exist in bereik table for some target groups:\n{result_df.to_string(index=False)}"


# SELECT * FROM [dbo].[tv.bereik_ster]
# WHERE flight_id not IN (
# SELECT flight_id
# FROM [dbo].[tv.flights_ster]
# );