import src.utils.dictionaries as mydict
import pandas as pd


def calculate_total_overlap(row, period_list=None) -> int:

    total_overlap = 0
    for period_start, period_end in period_list:
        overlap_start = max(row.start_date, pd.to_datetime(period_start))
        overlap_end = min(row.end_date, pd.to_datetime(period_end))
        overlap_days = max(0, (overlap_end - overlap_start).days + 1)
        total_overlap += overlap_days

    return total_overlap


def is_alcohol(advertiser, product, combined_dict):

    for adv, info in combined_dict.items():
        if adv.lower() == advertiser.lower():
            if (
                product.lower() in [p.lower() for p in info["products"]]
                and info["category"].lower() == "alcohol"
            ):
                return 1
    return 0


def is_kansspelen(advertiser, product, combined_dict):

    for adv, info in combined_dict.items():
        if adv.lower() == advertiser.lower():
            if (
                product.lower() in [p.lower() for p in info["products"]]
                and info["category"].lower() == "kansspelen"
            ):
                return 1
    return 0


def prep_dataframe(df_bereik: pd.DataFrame) -> pd.DataFrame:
    if "regio_grp" in df_bereik.columns:
        df_bereik["ster_grp"] = df_bereik["ster_grp"] + df_bereik["regio_grp"]
        df_bereik["ster_1bereik"] = (
            df_bereik["ster_1bereik"] + df_bereik["regio_1bereik"]
        )

    # remove rows where campaigns have 0 GRP for Ster
    df_bereik = df_bereik[
        (df_bereik["ster_1bereik"] != 0) | (df_bereik["ster_grp"] != 0)
    ]

    df = df_bereik[
        [
            "flight_id",
            "start_date",
            "end_date",
            "advertiser",
            "product",
            "daypart",
            "npo1_grp",
            "npo2_grp",
            "npo3_grp",
            "ster_grp",
            "npo1_1bereik",
            "npo2_1bereik",
            "npo3_1bereik",
            "ster_1bereik",
        ]
    ].reset_index(drop=True)

    df = df.pivot_table(
        index=["flight_id", "start_date", "end_date", "advertiser", "product"],
        columns="daypart",
        fill_value=0.0,
        values=[
            "npo1_grp",
            "npo2_grp",
            "npo3_grp",
            "npo1_1bereik",
            "npo2_1bereik",
            "npo3_1bereik",
            "ster_grp",
            "ster_1bereik",
        ],
        aggfunc="sum",
    ).reset_index()

    df.columns = [
        "_".join(col) if col[1] else col[0] for col in df.columns.to_flat_index()
    ]

    # Convert start_date and end_date to datetime objects and calculate required values
    df["start_date"] = pd.to_datetime(df["start_date"], format="%d%m%y")
    df["end_date"] = pd.to_datetime(df["end_date"], format="%d%m%y")

    # Apply function to create extra columns
    df["timef_start_month"] = df["start_date"].dt.month
    df["timef_end_month"] = df["end_date"].dt.month
    df["timef_start_year"] = df["start_date"].dt.year
    df["timef_end_year"] = df["end_date"].dt.year
    df["timef_start_week"] = df["start_date"].dt.strftime("%V").astype(int)
    df["timef_end_week"] = df["end_date"].dt.strftime("%V").astype(int)
    df["timef_start_day"] = df["start_date"].dt.day
    df["timef_end_day"] = df["end_date"].dt.day
    df["timef_duration_days"] = df.apply(
        lambda row: (row["end_date"] - row["start_date"]).days + 1, axis=1
    )

    # Calculate total overlap with olympics and WK/EK
    df["timef_olympic_period"] = df.apply(
        calculate_total_overlap, axis=1, period_list=(mydict.olympic_period_list)
    )
    df["timef_football_period"] = df.apply(
        calculate_total_overlap, axis=1, period_list=(mydict.football_wk_ek_list)
    )

    # Create meta columns for alcohol and kansspelen
    df["meta_alcohol_adv"] = df.apply(
        lambda row: is_alcohol(
            row["advertiser"], row["product"], mydict.alcohol_kansspelen_dict
        ),
        axis=1,
    )
    df["meta_kansspelen_adv"] = df.apply(
        lambda row: is_kansspelen(
            row["advertiser"], row["product"], mydict.alcohol_kansspelen_dict
        ),
        axis=1,
    )

    df["meta_hoofdspot_duration"] = mydict.spots_dict["meta_hoofdspot_duration"]
    df["meta_second_spot_duration"] = mydict.spots_dict["meta_second_spot_duration"]
    df["meta_tagon"] = mydict.spots_dict["meta_tagon"]

    df["timef_spreiding"] = mydict.spots_dict["timef_spreiding"]

    column_mapping = {
        "npo1_grp_primetime": "NPO_1_primetime_GRP",
        "npo1_grp_daynight": "NPO_1_daynight_GRP",
        "npo2_grp_primetime": "NPO_2_primetime_GRP",
        "npo2_grp_daynight": "NPO_2_daynight_GRP",
        "npo3_grp_primetime": "NPO_3_primetime_GRP",
        "npo3_grp_daynight": "NPO_3_daynight_GRP",
    }

    # Rename the columns using the dictionary
    df = df.rename(columns=column_mapping)

    return df
