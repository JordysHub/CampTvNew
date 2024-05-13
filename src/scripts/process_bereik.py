import camp_tv_new.src.utils.bereik_utils as bereik_utils

import pandas as pd
import time
from tqdm import tqdm
import warnings
import os
import ast

api_folder = './data/raw/api/bereik/'

def convert_to_list(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return string  # Return as is if not convertible to list

def process_row(row):
    new_row = row[:6].to_dict()
    for col_idx, cell in enumerate(row[6:], start=6):
        if isinstance(cell, float) and np.isnan(cell):
            continue
        # Extract information from the list
        first_part, second_part, third_part, value = cell
        # Generate column name based on second value in the list
        if second_part.endswith(' (%)'):
            second_part = second_part.split(' ')[0]
        else:
            second_part = 'grp'
        third_part = third_part.strip().replace(" ", "").lower()
        column_name = f"{third_part}_{second_part.strip().lower()}"
        # Add the value to the new row
        new_row[column_name] = value
    return new_row
