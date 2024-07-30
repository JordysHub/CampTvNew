import pytest
import camp_tv_new.src.utils.database_utils as db_utils


def test_no_flights_with_count_greater_than_3():
    #There cant be more than 3 of the same flights per tg (3 dayparts)
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

# def test_all_flights_exist_in_bereik_per_target_group(sql_query):
#     sql_query = """
#     SELECT DISTINCT f.target_group, f.flight_id
#     FROM [dbo].[tv.flights_ster] f
#     LEFT JOIN [dbo].[tv.bereik_ster] b ON f.flight_id = b.flight_id AND f.target_group = b.target_group
#     WHERE b.flight_id IS NULL;
#     """

#     result_df = db_utils.query_to_df(sql_query)
#     # Assert that the DataFrame is empty
#     assert result_df.empty, f"Found flights that do not exist in bereik table for some target groups:\n{result_df.to_string(index=False)}"


# SELECT * FROM [dbo].[tv.bereik_ster]
# WHERE flight_id not IN (
# SELECT flight_id
# FROM [dbo].[tv.flights_ster]
# );