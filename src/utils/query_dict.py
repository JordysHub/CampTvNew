import numpy as np

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

correction_factors = {
    ('13+', 0): 1.02,
    ('13+', 1): 0.93,
    ('13+', 2): 0.91,
    ('13+', 3): 0.92,
    ('20-49', 0): 0.96,
    ('20-49', 1): 0.94,
    ('20-49', 2): 0.91,
    ('20-49', 3): 0.94,
    ('25+', 0): 1.02,
    ('25+', 1): 0.93,
    ('25+', 2): 0.91,
    ('25+', 3): 0.93,
    ('25-39', 0): 0.94,
    ('25-39', 1): 0.96,
    ('25-39', 2): 0.94,
    ('25-39', 3): 0.96,
    ('25-54', 0): 0.95,
    ('25-54', 1): 0.92,
    ('25-54', 2): 0.91,
    ('25-54', 3): 0.93,
    ('25-59', 0): 0.96,
    ('25-59', 1): 0.93,
    ('25-59', 2): 0.89,
    ('25-59', 3): 0.92,
    ('25-59AB1', 0): 0.97,
    ('25-59AB1', 1): 0.93,
    ('25-59AB1', 2): 0.91,
    ('25-59AB1', 3): 0.93,
    ('25-67', 0): 0.97,
    ('25-67', 1): 0.92,
    ('25-67', 2): 0.89,
    ('25-67', 3): 0.92,
    ('25-67AB1', 0): 1.0,
    ('25-67AB1', 1): 0.94,
    ('25-67AB1', 2): 0.91,
    ('25-67AB1', 3): 0.93,
    ('3-12', 0): 0.98,
    ('3-12', 2): 0.97,
    ('3-12', 3): 0.98,
    ('30-65', 0): 0.96,
    ('30-65', 1): 0.91,
    ('30-65', 2): 0.89,
    ('30-65', 3): 0.92,
    ('35+', 0): 1.04,
    ('35+', 1): 0.93,
    ('35+', 2): 0.91,
    ('35+', 3): 0.94,
    ('35-59', 0): 0.97,
    ('35-59', 1): 0.92,
    ('35-59', 2): 0.88,
    ('35-59', 3): 0.92,
    ('35-64', 0): 0.97,
    ('35-64', 1): 0.91,
    ('35-64', 2): 0.88,
    ('35-64', 3): 0.92,
    ('50+', 0): 1.1,
    ('50+', 1): 0.95,
    ('50+', 2): 0.93,
    ('50+', 3): 0.96,
    ('6+', 0): 0.99,
    ('6+', 1): 0.94,
    ('6+', 2): 0.91,
    ('6+', 3): 0.92,
    ('68+', 0): 1.19,
    ('68+', 1): 0.98,
    ('68+', 2): 0.97,
    ('68+', 3): 1.01,
    ('7-12', 0): 0.98,
    ('7-12', 2): 0.97,
    ('7-12', 3): 0.99,
    ('B2B', 0): 0.94,
    ('B2B', 1): 0.87,
    ('B2B', 2): 0.85,
    ('B2B', 3): 0.89,
    ('BDS+KND', 0): 0.91,
    ('BDS+KND', 1): 0.92,
    ('BDS+KND', 2): 0.92,
    ('BDS+KND', 3): 0.95,
    ('BDS-KZ12', 0): 0.86,
    ('BDS-KZ12', 1): 0.92,
    ('BDS-KZ12', 2): 0.92,
    ('BDS-KZ12', 3): 0.97,
    ('BDS25-59', 0): 0.95,
    ('BDS25-59', 1): 0.92,
    ('BDS25-59', 2): 0.9,
    ('BDS25-59', 3): 0.92,
    ('BDS25-67', 0): 0.97,
    ('BDS25-67', 1): 0.92,
    ('BDS25-67', 2): 0.89,
    ('BDS25-67', 3): 0.91,
    ('M20-49', 0): 0.96,
    ('M20-49', 1): 0.93,
    ('M20-49', 2): 0.91,
    ('M20-49', 3): 0.94,
    ('M25-54', 0): 0.95,
    ('M25-54', 1): 0.92,
    ('M25-54', 2): 0.9,
    ('M25-54', 3): 0.92,
    ('M25-59', 0): 0.98,
    ('M25-59', 1): 0.93,
    ('M25-59', 2): 0.89,
    ('M25-59', 3): 0.92,
    ('M25-67', 0): 1.01,
    ('M25-67', 1): 0.92,
    ('M25-67', 2): 0.9,
    ('M25-67', 3): 0.92,
    ('M50+', 0): 1.1,
    ('M50+', 1): 0.94,
    ('M50+', 2): 0.92,
    ('M50+', 3): 0.97,
    ('V20-49', 0): 0.95,
    ('V20-49', 1): 0.94,
    ('V20-49', 2): 0.92,
    ('V20-49', 3): 0.94,
    ('V25-54', 0): 0.94,
    ('V25-54', 1): 0.93,
    ('V25-54', 2): 0.92,
    ('V25-54', 3): 0.94,
    ('V25-59', 0): 0.93,
    ('V25-59', 1): 0.91,
    ('V25-59', 2): 0.9,
    ('V25-59', 3): 0.92,
    ('V25-67', 0): 0.95,
    ('V25-67', 1): 0.9,
    ('V25-67', 2): 0.88,
    ('V25-67', 3): 0.91,
    ('V40+', 0): 1.06,
    ('V40+', 1): 0.94,
    ('V40+', 2): 0.91,
    ('V40+', 3): 0.95,
    ('V50+', 0): 1.1,
    ('V50+', 1): 0.95,
    ('V50+', 2): 0.92,
    ('V50+', 3): 0.96}

bucket_bounds = {
    '13+': [0., 30., 70., 150., np.inf],
    '20-49': [0., 10., 30., 70., np.inf],
    '25+': [0., 40., 80., 160., np.inf],
    '25-39': [0., 10., 20., 50., np.inf],
    '25-54': [0., 20., 40., 80., np.inf],
    '25-59': [0., 20., 40., 100., np.inf],
    '25-59AB1': [0., 20., 40., 80., np.inf],
    '25-67': [0., 30., 60., 120., np.inf],
    '25-67AB1': [0., 20., 50., 100., np.inf],
    '3-12': [0., 10., 10., 30., np.inf],
    '30-65': [0., 30., 60., 120., np.inf],
    '35+': [0., 40., 90., 170., np.inf],
    '35-59': [0., 20., 50., 110., np.inf],
    '35-64': [0., 30., 60., 130., np.inf],
    '50+': [0., 40., 90., 170., np.inf],
    '6+': [0., 30., 70., 140., np.inf],
    '68+': [0., 40., 100., 170., np.inf],
    '7-12': [0., 10., 10., 30., np.inf],
    'B2B': [0., 20., 40., 90., np.inf],
    'BDS+KND': [0., 20., 40., 80., np.inf],
    'BDS-KZ12': [0., 20., 30., 70., np.inf],
    'BDS25-59': [0., 20., 50., 100., np.inf],
    'BDS25-67': [0., 30., 60., 130., np.inf],
    'M20-49': [0., 10., 30., 70., np.inf],
    'M25-54': [0., 20., 40., 80., np.inf],
    'M25-59': [0., 20., 40., 100., np.inf],
    'M25-67': [0., 20., 60., 120., np.inf],
    'M50+': [0., 40., 90., 170., np.inf],
    'V20-49': [0., 10., 30., 70., np.inf],
    'V25-54': [0., 20., 40., 80., np.inf],
    'V25-59': [0., 20., 50., 100., np.inf],
    'V25-67': [0., 30., 60., 120., np.inf],
    'V40+': [0., 40., 90., 180., np.inf],
    'V50+': [0., 40., 100., 180., np.inf]
}
