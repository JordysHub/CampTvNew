class Queries:
    @staticmethod
    def get_missing_flights_per_target_group(target_groups):
        target_groups_str = ", ".join(f"'{tg}'" for tg in target_groups)
        return f"""
        WITH AllCombinations AS (
            SELECT
                f.flight_id,
                b.target_group
            FROM [dbo].[tv.flights_ster] f
            CROSS JOIN (
                SELECT DISTINCT target_group
                FROM [dbo].[tv.bereik_ster]
                WHERE target_group IN ({target_groups_str})
            ) b
        ),
        MissingPairs AS (
            SELECT
                ac.flight_id,
                ac.target_group
            FROM AllCombinations ac
            LEFT JOIN [dbo].[tv.bereik_ster] b ON ac.flight_id = b.flight_id AND ac.target_group = b.target_group
            WHERE b.flight_id IS NULL
        ),
        AggregatedMissingTargetGroups AS (
            SELECT
                flight_id,
                STRING_AGG(target_group, ', ') AS missing_target_groups
            FROM MissingPairs
            GROUP BY flight_id
        )
        SELECT f.[flight_id]
            ,[advertiser]
            ,[product]
            ,[start_date]
            ,[end_date]
            ,[campaign_duration]
            ,[npo1_grp]
            ,[npo2_grp]
            ,[npo3_grp]
            ,[regio_grp]
            ,[ster_grp]
            ,[mock_campaign]
            ,[alcohol_kansspelen],
            COALESCE(am.missing_target_groups, '') AS missing_target_groups
        FROM [dbo].[tv.flights_ster] f
        LEFT JOIN AggregatedMissingTargetGroups am ON f.flight_id = am.flight_id
        WHERE am.missing_target_groups IS NOT NULL
        order by start_date
        """

    @staticmethod
    def delete_bereik_flights_which_dont_match():
        #
        return """
        SELECT DISTINCT
            t1.flight_id
        FROM
            [dbo].[tv.bereik_ster] t1
        JOIN
            [dbo].[tv.flights_ster] t2
        ON
            t1.flight_id = t2.flight_id
        WHERE
            t1.campaign_duration != t2.campaign_duration
        """

    @staticmethod
    def get_existing_dates_from_spots():
        #
        return """
        SELECT DISTINCT [date]
        FROM [dbo].[tv.spots_ster]
        """

"""
# delete duplicates

WITH CTE AS (
    SELECT
        flight_id,
        target_group,
        campaign_duration,
        daypart,
        total_grp,
        ster_grp,
        regio_grp,
        npo1_grp,
        ROW_NUMBER() OVER (
            PARTITION BY
                flight_id,
                target_group,
                campaign_duration,
                daypart,
                total_grp,
                ster_grp,
                regio_grp,
                npo1_grp
            ORDER BY flight_id) AS rn
    FROM [dbo].[tv.bereik_ster]
)
DELETE FROM CTE
WHERE rn > 1;

"""