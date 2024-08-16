class Queries:
    @staticmethod
    def get_missing_flights_per_target_group(target_groups):
        target_groups_str = ', '.join(f"'{tg}'" for tg in target_groups)
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
    def delete_overlapping_flights():
    # When fetching older data, these newly calculated campaigns can overlap with the already existing campaigns.
        return """
        WITH overlapping_campaigns AS (
        SELECT
            old.flight_id AS old_flight_id,
            new.flight_id AS new_flight_id
        FROM
            [dbo].[tv.flights_ster] AS old
        JOIN
            [dbo].[tv.flights_ster] AS new
        ON
            old.advertiser = new.advertiser
            AND old.product = new.product
            AND old.end_date = new.end_date
            AND new.start_date < old.start_date
        )
        DELETE FROM [dbo].[tv.flights_ster]
        WHERE flight_id IN (
            SELECT old_flight_id
            FROM overlapping_campaigns
        );
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













query_dict = {
    'get_flights_ster': '''
        SELECT flight_id, advertiser, product, start_date, end_date, campaign_duration, mock_campaign, ster_grp FROM [dbo].[tv.flights_ster]''',
    'get_flights': '''
        SELECT flight_id, advertiser, product, start_date, end_date, campaign_duration, mock_campaign, ster_grp FROM [dbo].[tv.flights]''',

    'get_existing_campaign_data_ster': '''
        SELECT DISTINCT flight_id, target_group FROM [dbo].[tv.bereik_ster];
    ''',

    'get_existing_campaign_data': '''
        SELECT DISTINCT flight_id, target_group FROM [dbo].[tv.bereik];
    ''',


    'get_missing_flights_all': '''
        SELECT f.flight_id
        FROM [dbo].[tv.flights_ster] f
        LEFT JOIN [dbo].[tv.bereik_ster] b ON f.flight_id = b.flight_id
        WHERE b.flight_id IS NULL
    ''',

    'collect_mock_flights': '''
    SELECT flight_id, advertiser, product, start_date, end_date, campaign_duration, mock_campaign, ster_grp
    FROM [dbo].[tv.flights]
    WHERE mock_campaign = 1
    ''',

    'get_existing_campaign_data': '''
    SELECT DISTINCT flight_id, target_group
    FROM [dbo].[tv.bereik_ster];
    ''',

    'get_existing_dates_from_spots': '''
    SELECT DISTINCT [date]
    FROM [dbo].[tv.spots_ster]
    ''',

    'get_bereik':
        '''SELECT flight_id, target_group, campaign_duration, daypart FROM [dbo].[tv.bereik_ster] WHERE target_group = :target_group''',
    'get_bereik_model':'''
        SELECT b.flight_id, f.start_date, f.end_date, b.target_group, b.campaign_duration, b.daypart, b.total_grp, b.ster_grp, b.regio_grp, b.npo1_grp, b.npo2_grp, b.npo3_grp, b.[ster_1+]
        FROM [dbo].[tv.bereik_ster] b
        LEFT JOIN [dbo].[tv.flights_ster] f ON b.flight_id = f.flight_id
        where b.ster_grp > 0 and target_group = :target_group and start_date >= :start_date and end_date <= :end_date
        ''',

    'delete_double_entries': '''
        WITH CTE AS (
        SELECT
            flight_id,
            target_group,
            campaign_duration,
            daypart,
            total_grp,
            ROW_NUMBER() OVER (PARTITION BY flight_id, target_group, campaign_duration, daypart, total_grp ORDER BY (SELECT NULL)) AS row_num
        FROM [dbo].[tv.bereik_ster]
        )
        DELETE FROM CTE
        WHERE row_num > 1;
    '''
}








"""
IF OBJECT_ID('tempdb..#temp_results') IS NOT NULL
    DROP TABLE #temp_results;

CREATE TABLE #temp_results (
    flight_id VARCHAR(50),
    target_group VARCHAR(50),
    campaign_duration INT,
    daypart VARCHAR(50)
);

-- Step 2: Declare a list of target groups
DECLARE @target_groups TABLE (target_group VARCHAR(50));

-- Insert your target groups into the table variable
INSERT INTO @target_groups (target_group)
VALUES ('25-67'), ('B2B'), ('20-49'), ('3-12'), ('30-65'), ('35+'),
        ('35-59'), ('35-64'), ('50+'), ('6+'), ('68+'), ('7-12'),
        ('BDS 25-59'), ('BDS 25-67'), ('13+'), ('25+'), ('25-39'),
        ('25-54'), ('25-59'), ('25-59AB1'), ('25-67AB1'), ('BDS KZ12'),
        ('BDS+KND'), ('DAG 25-59'), ('M 20-49'), ('M 25-54'), ('M 25-59'),
        ('M 25-67'), ('M 50+'), ('V 20-49'), ('V 25-54'), ('V 25-59'),
        ('V 25-67'), ('V 40+'), ('V 50+'), ('W1 45-75')

-- Step 3: Loop through each target group and insert the results into the temporary table
DECLARE @current_group VARCHAR(50);

DECLARE group_cursor CURSOR FOR
SELECT target_group FROM @target_groups;

OPEN group_cursor;
FETCH NEXT FROM group_cursor INTO @current_group;

WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @sql NVARCHAR(MAX);
    SET @sql = N'
    INSERT INTO #temp_results (flight_id, target_group, campaign_duration, daypart)
    SELECT flight_id, target_group, campaign_duration, daypart
    FROM [dbo].[tv.bereik]
    WHERE target_group = @current_group
    AND flight_id IN (
        SELECT flight_id
        FROM [dbo].[tv.bereik]
        WHERE target_group = @current_group
        GROUP BY flight_id
        HAVING COUNT(*) > 3
    );';

    EXEC sp_executesql @sql, N'@current_group VARCHAR(50)', @current_group;

    FETCH NEXT FROM group_cursor INTO @current_group;
END;

CLOSE group_cursor;
DEALLOCATE group_cursor;

-- Step 4: Select all results from the temporary table
SELECT * FROM #temp_results;

-- Step 5: Drop the temporary table
DROP TABLE #temp_results;

"""