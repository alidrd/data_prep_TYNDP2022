"""
Used to read Renewables Ninja data.
"""

import pandas as pd
import numpy as np
import os


# define paths ---------------------------------------------------------------
source_data_dir = r"C:/Users\daru/OneDrive - ZHAW/EDGE\data_sources/ninja//"
target_output_dir  = r"inputs_to_model//RES_ninja//"

# define ranges ----------------------------------------------------------

climate_year_list = [1995, 2008, 2009]

# load data ------------------------------------------------------------------

# if target_output_dir does not exist, create it
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)


AF_dict = {}

wind_df = pd.read_csv(source_data_dir + "CH_wind.csv", skiprows=2)

# following the column time, read data for years in [1995, 2008, 2009]
# the output should be 3 different dataframes, each for a different year
# the dataframes should be stored in a dictionary with the year as key

for year in climate_year_list:
    df = wind_df[wind_df["time"].str.contains(str(year))].copy()

    # rename the column "time" to "t" and replace values with t_1, t_2, t_3, ...
    df.rename(columns={"time": "t"}, inplace=True)
    df["t"] = ["t_" + str(i) for i in range(1, len(df) + 1)]

    AF_dict[year] = df.iloc[0:8760, :]
    AF_dict[year].to_csv(target_output_dir + "windon_w" + str(year) + ".csv", index=False)