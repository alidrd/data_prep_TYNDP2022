import pandas as pd
import os

# define paths ---------------------------------------------------------------
source_data_dir = r"demand//"
target_output_dir = r"holiday_analysis//"

# define years ---------------------------------------------------------------

# years 
run_year = [2050,] # 2030, 2025, 2040


# define years ---------------------------------------------------------------
# years for which capacity factor is available
PECD_data_years_list = [2050,] # 2030, 2025, 2040

# target climate years
climate_years_list = [2008, 2009, 1995]

# policy scenario
EU_policy_dict = {
    "DE": "DistributedEnergy" ,
    "GA": "GlobalAmbition",
    }

EU_policy_spaced_dict = {
    "DE": "Distributed Energy" ,
    "GA": "Global Ambition",
    }


# functions      -----------------------------------------------------------
#TODO: check here
def identify_holidays(time_series):
    # Extract numerical part of the index and convert to integers
    time_series.index = time_series.index.str.split('_').str[1].astype(int)
    
    # Calculate the average daily consumption
    daily_avg = time_series.groupby(time_series.index // 24).mean()

    holiday_indices = pd.Series(index=daily_avg.index)

    holiday_treshold = 0.9
    # loop over the days
    for day in range(1, len(daily_avg)):
        # compare the consumption of the day with the consumption of last 7 days and next 7 days
        if daily_avg[day] < daily_avg[day-1] * holiday_treshold:
            # if the consumption is significantly lower than the consumption of last 7 days and next 7 days, then it is a holiday
            holiday_indices[day] = 0
        else:
            holiday_indices[day] = 1
    holiday_indices.to_clipboard()

    
    # Calculate a threshold for identifying holidays
    threshold = daily_avg.mean() * 0.8  # Adjust the threshold multiplier as needed
    
    # Identify indices where consumption is significantly lower than the threshold
    holiday_indices = daily_avg[daily_avg < threshold].index
    
    return holiday_indices

# read in the data and write to csvs ----------------------------------------------------------
# if target_output_dir does not exist, create it
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)

for run_year in PECD_data_years_list:
    for EU_policy, EU_policy_long in EU_policy_spaced_dict.items():
        for climate_year in climate_years_list:
            holidays = pd.DataFrame()
            EU_policy_no_spaces = EU_policy_dict[EU_policy]
            print("Finding holidays for demand time series of ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy, 90*"-")
            # read demand data from csv file
            demand_df = pd.read_csv(source_data_dir + "demand_" + EU_policy_no_spaces + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=0)
            for column in demand_df.columns:
                # demand_df[column] = pd.to_numeric(demand_df[column], errors='coerce')
                holidays[column] = identify_holidays(demand_df[column])
            # write the data to csv file
            
            holidays.to_csv(target_output_dir + "holidays_" + EU_policy_no_spaces + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            # capacity_all_df.to_csv(target_output_dir + "capacity_" + EU_policy_no_spaces + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)            
