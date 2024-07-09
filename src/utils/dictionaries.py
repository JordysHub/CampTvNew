from datetime import datetime, date

target_groups = ['25-67', 'B2B', '20-49', '3-12', '30-65', '35+', '35-59', '35-64', '50+', '6+', '68+',
                 '7-12', 'BDS25-59', 'BDS25-67', '13+', '25+', '25-39', '25-54', '25-59', '25-59AB1', '25-67AB1',
                 'BDS+KND', 'DAG 25-59', 'M20-49', 'M25-54', 'M25-59',
                 'M25-67', 'M50+', 'V 20-49', 'V 25-54', 'V 25-59', 'V 25-67', 'V 40+',
                 'V 50+', 'W1 45-75', 'BDS KZ12']

# , '30-60 EH', '35-59 AB1'

rename_dict = {
    'BDS KZ12': 'BDS-KZ12',
    'V 20-49': 'V20-49',
    'V 25-54': 'V25-54',
    'V 25-59': 'V25-59',
    'V 25-67': 'V25-67',
    'V 40+': 'V40+',
    'V 50+': 'V50+',
    # 'W1 45-75': 'W145-75'
}

alcohol_kansspelen_dict = {
    "Bavaria": {"products": ["Bavaria", "Palm", "Swinckels"], "category": "Alcohol"},
    "Carlsberg international": {"products": ["Carlsberg"], "category": "Alcohol"},
    "Duvel moortgat": {"products": ["Duvel"], "category": "Alcohol"},
    "Gulpener bierbrouwerijen": {"products": ["Gulpener"], "category": "Alcohol"},
    "Heineken": {
        "products": [
            "Amstel",
            "Brand",
            "Desperados",
            "Heineken",
            "Wieckse",
            "Apple bandit",
            "Jillz",
            "Strongbow",
            "Vrienden van amstel live",
            "Affligem",
        ],
        "category": "Alcohol",
    },
    "Ab Inbev": {"products": ["Hertog jan", "Jupiler", "Leffe", "Bud", "Corona", "Tripel Karmeliet", "Tripel karmeliet"], "category": "Alcohol"},
    "Koninklijke grolsch": {"products": ["Grolsch", "Kornuit"], "category": "Alcohol"},
    "Lidl": {"products": ["Kordaat"], "category": "Alcohol"},
    "Palm brouwerij": {"products": ["Palm"], "category": "Alcohol"},
    "Warsteiner": {"products": ["Warsteiner"], "category": "Alcohol"},
    "Bacardi": {"products": ["Bacardi", "Martini", "William lawson", "Martini", "Bacardi", "Eristoff"], "category": "Alcohol"},
    "Maxxium": {"products": ["The famous grouse", "Licor 43", "The famous grouse", "Russian standard vodka"], "category": "Alcohol"},
    "Hooghoudt": {"products": ["Hooghoudt"], "category": "Alcohol"},
    "De lotto": {"products": ["Lotto"], "category": "Kansspelen"},
    "Eredivisie": {"products": ["Nationale postcode loterij"], "category": "Kansspelen"},
    "Gran casino tiel": {"products": ["Gran casino tiel"], "category": "Kansspelen"},
    "Holding nationale goede doelen loterijen": {
        "products": ["Bankgiro loterij", "Nationale postcode loterij", "Postcode lottery", "Sponsor bingo loterij", "Vrienden loterij"],
        "category": "Kansspelen",
    },
    "Holland casino": {"products": ["Holland casino"], "category": "Kansspelen"},
    "Interbest": {"products": ["Freeway"], "category": "Kansspelen"},
    "Jvh gaming & entertainment": {"products": ["Jack's casino"], "category": "Kansspelen"},
    "Nederlandse loterij": {
        "products": ["Eurojackpot", "Krasloten", "Lotto", "Lucky day", "Nederlandse loterij", "Staatsloterij", "Toto"],
        "category": "Kansspelen",
    },
    "Nederlandse staatsloterij": {"products": ["Miljoenenspel"], "category": "Kansspelen"},
    "A brand new day drinks company": {"products": ["Aperol"], "category": "Alcohol"},
    "Diageo": {"products": ["Baileys", "Johnnie walker", "Captain morgan", "Smirnoff"], "category": "Alcohol"},
    "Disaronno international": {"products": ["Disaronno", "Tia maria"], "category": "Alcohol"},
    "International marques": {"products": ["Campari"], "category": "Alcohol"},
    "Pernod ricard": {"products": ["Malibu", "Jameson", "Beefeater", "Havana club"], "category": "Alcohol"},
    "Baarsma wines": {"products": ["0.0%", "Canei"], "category": "Alcohol"},
    "Casillero del diablo": {"products": ["Casillero del diablo"], "category": "Alcohol"},
    "Castel frres": {"products": ["Famille castel"], "category": "Alcohol"},
    "Fair trade original": {"products": ["Fair trade original"], "category": "Alcohol"},
    "Treasury wine estates": {"products": ["Lindemans"], "category": "Alcohol"},
    "Walraven & sax": {"products": ["Hardy's"], "category": "Alcohol"},
    "Monnik dranken bv, de": {"products": ["Pravda"], "category": "Alcohol"},
    "e-luscious nederland": {"products": ["Wijnvoordeel.nl"], "category": "Alcohol"},
    "poppodium tilburg 013": {"products": ["Poppodium tilburg 013"], "category": "unknown"},
    "fair play centers": {"products": ["Fair play casino"], "category": "Kansspelen"},
    "hillenaar events": {"products": ["Kamasutra"], "category": "unknown"},
    "groupm worldwide": {"products": ["Action"], "category": "unknown"},
    "reckitt benckiser": {"products": ["Durex"], "category": "unknown"},
    "brown-forman beverages": {"products": ["Jack daniels"], "category": "Alcohol"},
    "loversland": {"products": ["Loversland"], "category": "unknown"},
    "beer in a box bv": {"products": ["Beer in a box"], "category": "Alcohol"},
}

olympic_period_list = [[date(2024, 7, 26), date(2024, 8, 11)],
                       [date(2028, 7, 21), date(2028, 8, 6)]]

football_wk_ek_list = [[date(2022, 11, 20), date(2022, 12, 18)],
                       [date(2024, 6, 14), date(2024, 7, 14)],
                       [date(2026, 6, 11), date(2026, 7, 19)]]
