import pandas as pd
import os
import plotly.graph_objects as go

year_target = 2050 # 2040
mode = "demand" # "demand" or "generation"	
demand_mode = "normal" # "normal" or "no_weather_year"

target_weather_year = 1984
if mode == "demand":
    if demand_mode == "normal":
        dir_target = r"C:\Users\daru\switchdrive\SA2022\Data\01_source_data\Prognos to SA Team\2022-02-11 Load profiles weather years\Lastprofile_Wetterjahre\1982\EPCH_ZEROBasis_Normal_1982"
        dir_target = dir_target.replace("1982", str(target_weather_year))
    elif demand_mode == "no_weather_year":
        dir_target = r"C:\Users\daru\switchdrive\SA2022\Data\01_source_data\Prognos to SA Team\Used_data_for_analysis\EPCH-ZEROBasis\Nachfrage"

elif mode == "generation":
    dir_target = r"C:\Users\daru\switchdrive\SA2022\Data\01_source_data\Prognos to SA Team\Used_data_for_analysis\EPCH-ZEROBasis\Erzeugung"

# in dir_target, replce 1982 with target_weather_year


# create an empty dataframe
data_all_df = pd.DataFrame()

# get the list of all files in the dir_target
files_list = os.listdir(dir_target)

for file_name in files_list:
    # read csv file
    if mode == "demand":
        data_df = pd.read_csv(dir_target + "\\" + file_name)
    elif mode == "generation":
        data_df = pd.read_csv(dir_target + "\\" + file_name, sep=";")

    # keep the rows whose column jahr is equal to year_target
    data_df = data_df[data_df["jahr"] == year_target]

    # drop the column jahr
    data_df = data_df.drop(columns=["jahr"])

    # pivot the table, where values are stored in the column "wert" and the column "stunde" is the new index
    data_df = data_df.pivot(index="stunde", columns="region", values="wert")

    # sum all values in the same row of data_df and add it to the data_all_df with the same index and column name file_name
    # 
    if mode == "demand":
        if demand_mode == "normal":
            name = file_name.split("_")[4] + "_" + file_name.split("_")[5]
        elif demand_mode == "no_weather_year":
            name = file_name.split("_")[3] + "_" + file_name.split("_")[4]
    elif mode == "generation":
        name = file_name.split("_")[3]
    data_all_df[name] = data_df.sum(axis=1)

# add a column sum to data_all_df, where the values are the sum of all values in the same row
data_all_df["sum"] = data_all_df.sum(axis=1)

# save the data_all_df as csv file called mode + "_aggregated.csv"
data_all_df.to_csv(mode + "_aggregated.csv")

# provide a summary statistics of columns in data_all_df 
stats = data_all_df.describe()

# calculate the sum of values in each column of data_all_df
sums = data_all_df.sum(axis=0)

# merge  sums and stats into one dataframe. The columns are the same as in stats
stats_sums = pd.concat([sums, stats.T], axis=1)

# save stats_sums as csv file
stats_sums.to_csv(mode + "_aggregated_stats_sums.csv")

# plot the data_all_df using plotly 
fig = go.Figure()
for column in data_all_df.columns:
    fig.add_trace(go.Scatter(x=data_all_df.index, y=data_all_df[column], name=column))
fig.show()