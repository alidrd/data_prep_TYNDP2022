"""	
This script prepares the following data for the model:
- capacities of power plants
- annual generation of power plants
- annual demand of electrolysis

Important:
run electrolysis_demand_read.py and tyndp22_flows.py before running this script

"""
import subprocess
import os
import pandas as pd


target_output_dir = r"inputs_to_model//"
input_dir = r"annuals_cap_dem_gen_imp//"


#%% parameters -------------------------------------------------------------------------------------
# define target scenarios/years/climate years -------------------------------------------------------
run_year_list = [2050, 2040, 2030] # 2030, 2025, 2040

# target climate years
climate_years_list = [2008, 2009, 1995]

# policy scenario
EU_policy_spaced_dict = {
    "DE": "Distributed Energy" ,
    "GA": "Global Ambition",
    }

merge_some_countries = True # if True, the data for several regions in Italy (and also Luxembourg) are merged into IT00 (and LU00)
target_merge_countries = [
    # "IT", # unnecessary to include IT, as data only has IT00 already
    "LU",
    # "PL", # unnecessary to include IT, as data only has IT00 already
    # "FR",   # there is FR15 only in capacity data (only small dsr and battery)
    ] # countries to merge


# create target_output_dir if it does not exist
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)

# technology mapping -------------------------------------------------------------------------------

technology_dict = {
                "Battery": "battery",
                "Biomass": "biomass",  
                "Other RES":"biomass",
                "CHP"  :"chp",
                "Gas"  :"gas",
                "Other Non RES"  :"gas",
                "Oil": "oil",
                "DSR": "dsr",
                "Coal & Lignite": "hardcoal",                
                "Nuclear": "nuclear",
                # "Hydro": "dam",
                # "Hydro Pump Storage": "psp_open",
                # "PSP_Closed": "psp_close",
                "Solar": "pvrf",
                "Wind Onshore": "windon",
                "Wind Offshore": "windof",
 
}
# to separate the infeed technologies from the rest
RES_technologies = ["windon", "windof", "pvrf"]

# items that will be summed up to calculate the total electrolyzer demand
columns_electrolyzer = ["Electrolysis Config 1",  "Electrolysis Config 2",  "Electrolysis Config 3",  "Electrolysis Config 4"]
columns_basedemand = ["Transmission Node", "Transport Node", "Prosumer Node"]

# Functions -----------------------------------------------------------------------------------------
def merge_regions_in_country_capacity(df_gen):
    for country in target_merge_countries:
        # find the subset of rows in df_gen in which the column node starts with country
        df_country = df_gen[df_gen.index.get_level_values(0).str.startswith(country)]

        # remove all rows in df_country from df_gen
        df_gen = df_gen[~df_gen.index.get_level_values(0).str.startswith(country)]

        # reset the index
        df_country = df_country.reset_index()

        # rename node column to country + "00"
        df_country["node"] = country + "00"

        # rename nodeline column to country + "00"
        df_country["nodeline"] = country + "00"

        # group by node  fuel scenario  weather_year and run_year
        df_country = df_country.groupby(["node", "nodeline", "fuel"]).sum()

        # add df_country to df_gen
        df_gen = pd.concat([df_gen, df_country])

        df_gen.to_clipboard()

    return df_gen
#%%  generation and capacity data  (read and export) -------------------------------------------------
# create annual generation.csv -----------------------------------------------------------------------
# read in the data
# generation_all_df = pd.DataFrame(columns=["scenario", "zone", "zone_long", "tech", "weather_year", "2025", "2030", "2040", "2050"])

generation_all_df = pd.DataFrame()
capacity_all_df = pd.DataFrame()


for scen_short, scen_long, in EU_policy_spaced_dict.items():
    scen_long_no_space = scen_long.replace(" ", "")
    for run_year in run_year_list:
        for climate_year in climate_years_list:
            # generation data -------------------------------------------------------------------------------
            df_gen = pd.read_csv(input_dir + "generation_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0, 1, 2])
            
            # apply the mapping of technologies between models: replace all keys in technology_dict with the corresponding values
            df_gen = df_gen.rename(index=technology_dict)
            # merging some regions Luxembourg to only have values for LU00
            if merge_some_countries:
                df_gen = merge_regions_in_country_capacity(df_gen)

            # add columns for scenario, zone, zone_long, tech, weather_year
            df_gen["scenario"] = scen_long_no_space
            df_gen["weather_year"] = climate_year
            df_gen["run_year"] = run_year

            # merge df_gen with generation_all_df based on index, add columns from df_gen to generation_all_df
            generation_all_df = pd.concat([generation_all_df, df_gen])

        # ---------------------------------------------------------------------------------------------
        # capacity data -------------------------------------------------------------------------------
        df_cap = pd.read_csv(input_dir + "capacity_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0, 1, 2])

        # remove CH plants (prognos data will be used)
        # remove rows that have CH00 as node
        df_cap = df_cap[~df_cap.index.get_level_values(0).str.startswith("CH")]

        if merge_some_countries:
            df_cap = merge_regions_in_country_capacity(df_cap)

        # if there is a cell with value "q", replace it with float 12543.28 (one missing data issue for CZ00H2R1	Global Ambition 2050)
        df_cap = df_cap.replace("q", float(12543.28))

        # apply the mapping of technologies between models: replace all keys in technology_dict with the corresponding values
        df_cap = df_cap.rename(index=technology_dict)

        # add columns for scenario, zone, zone_long, tech
        df_cap["scenario"] = scen_long_no_space
        df_cap["run_year"] = run_year

        #  values in the column capacity should be of type numpy.float64
        df_cap["capacity"] = df_cap["capacity"].astype("float64")

        # merge df_cap with capacity_all_df based on index, add columns from df_cap to capacity_all_df
        capacity_all_df = pd.concat([capacity_all_df, df_cap])



         
# reorder and export dataframes ---------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
            
# export generation.csv ----------------------------------------------------------------------------
generation_all_ordered_df = generation_all_df.reset_index()

generation_all_ordered_df = generation_all_ordered_df.pivot_table(index=['node', 'fuel', 'scenario', 'weather_year'], 
                                                  columns='run_year', 
                                                  values='generation',
                                                  aggfunc='sum').reset_index()

# rename columns node to zone, nodeline to zone_long, fuel to tech
generation_all_ordered_df = generation_all_ordered_df.rename(columns={"node": "zone", "nodeline": "zone_long", "fuel": "tech"})

# use the following columns as the first columns in the dataframe and keep the order of the rest: scenario,	zone,	tech,	weather_year
desired_columns = ['scenario', 'zone', 'tech', 'weather_year']
generation_all_ordered_df = generation_all_ordered_df[desired_columns + [col for col in generation_all_ordered_df.columns if col not in desired_columns]]

generation_all_ordered_df.to_csv(target_output_dir + "generation.csv", encoding="utf-8", index=False)


# export nonhydro_capacities_gen.csv  and  plants_non_hydro.csv---------------------------------------------------------------

capacity_all_ordered_df = capacity_all_df.reset_index()

# find duplicate rows that are not duplicated with regard to columns node, nodeline, run_year
capacity_all_ordered_df[capacity_all_ordered_df.duplicated(subset=["node", "nodeline", "run_year"], keep=False)]

# add a column with the name of the power plant
capacity_all_ordered_df["name"] = capacity_all_ordered_df["node"] + "_" + capacity_all_ordered_df["fuel"]

# separate RES from others ------------------------------------
# find the subset of rows in capacity_all_ordered_df in which the column tech in RES_technologies 
capacity_res_df = capacity_all_ordered_df[capacity_all_ordered_df["fuel"].isin(RES_technologies)]

# remove capacity_res_df from capacity_all_ordered_df
capacity_conv_ordered_df = capacity_all_ordered_df[~capacity_all_ordered_df["fuel"].isin(RES_technologies)]

# plants_non_hydro.csv whiche needs to include the following info
# index	node-----	market----	plant_type----- 	tech	upperwn	lowerwn	eta	eta_pump	n_redispatch
plants_list = pd.DataFrame(columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])

plants_list["index"] = capacity_conv_ordered_df["name"]
plants_list["node"] = capacity_conv_ordered_df["node"]
plants_list["market"] = capacity_conv_ordered_df["node"]
plants_list["plant_type"] = "Conventional"
plants_list["tech"] = capacity_conv_ordered_df["fuel"]

# remove duplicates from plants_list, keep the first occurrence
plants_list = plants_list.drop_duplicates()

plants_list[plants_list["node"] == "SE04"]
capacity_conv_ordered_df[(capacity_conv_ordered_df["node"] == "SE04") & (capacity_conv_ordered_df["fuel"] == "gas")]



plants_list.to_csv(target_output_dir + "plants_non_hydro.csv", encoding="utf-8", index=False)



# export capacity_conv_ordered_df---------------------------------------------------------------------
# pivot and aggregate the data
capacity_conv_ordered_df = capacity_conv_ordered_df.pivot_table(index=['node', 'name', 'scenario'], #TODO order
                                                    columns='run_year', 
                                                    values='capacity',
                                                    aggfunc='sum').reset_index()

capacity_conv_ordered_df[(capacity_conv_ordered_df["node"] == "SE04")]

# remove the column node
capacity_conv_ordered_df = capacity_conv_ordered_df.drop(columns="node")

for plants in plants_list.loc[:,"index"]:
    for scenario in EU_policy_spaced_dict.values():
        scen = scenario.replace(" ", "")
        # if a row with the name of the plant and the scenario does not exist, add it with 0 values
        if capacity_conv_ordered_df[(capacity_conv_ordered_df["name"] == plants) & (capacity_conv_ordered_df["scenario"] == scen)].empty:
            new_row = pd.DataFrame([[plants, scen, 0, 0, 0]], columns=capacity_conv_ordered_df.columns)
            capacity_conv_ordered_df = pd.concat([capacity_conv_ordered_df, new_row], ignore_index=True)


# export the dataframe
capacity_conv_ordered_df.to_csv(target_output_dir + "nonhydro_capacities_gen.csv", encoding="utf-8", index=False)

# export capacity_res_df---------------------------------------------------------------------
# pivot and aggregate the data
capacity_res_df = capacity_res_df.pivot_table(index=["name", "node", "fuel", "scenario"],
                                                    columns='run_year', 
                                                    values='capacity',
                                                    aggfunc='sum').reset_index()

# rename fuel to tech
capacity_res_df = capacity_res_df.rename(columns={"fuel": "tech"})

# manual adjustments --------------------------------------------------------------------------------
# if for a row, value of column 2050 is NaN, replace it with the value of column 2040
capacity_res_df.loc[capacity_res_df[2050].isna(), 2050] = capacity_res_df.loc[capacity_res_df[2050].isna(), 2040]
# should affect the following rows:
# DKKF_windof	DKKF	windof	GlobalAmbition	605	605	
# CH00_pvrf	CH00	pvrf	GlobalAmbition	5487	6250	

# if for a row, value of column 2040 is NaN, and value of 2030 is not Nan, replace value of 2040 with the value of column 2050
capacity_res_df.loc[capacity_res_df[2040].isna() & ~capacity_res_df[2030].isna(), 2040] = capacity_res_df.loc[capacity_res_df[2040].isna() & ~capacity_res_df[2030].isna(), 2050]

# add rows below to add some offshore wind capacity to DEKF (as much as planned in NationalTrends 2040)
# DEKF_windof DEKF windof GlobalAmbition 336 336 336
# DEKF_windof DEKF windof DistributedEnergy 336 336 336
new_rows = pd.DataFrame([
    {'name': 'DEKF_windof', 'node': 'DEKF', 'tech': 'windof',    'scenario': 'GlobalAmbition', 2030: 336, 2040: 336, 2050: 336},
    {'name': 'DEKF_windof', 'node': 'DEKF', 'tech': 'windof', 'scenario': 'DistributedEnergy', 2030: 336, 2040: 336, 2050: 336}
])

capacity_res_df = pd.concat([capacity_res_df, new_rows], ignore_index=True)



# export the dataframe
capacity_res_df.to_csv(target_output_dir + "res_capacities_TYNDP22.csv", encoding="utf-8", index=False)

#%% electrolyzer demand data (read and export) ---------------------------------------------------------------------

demand_all_df = pd.DataFrame()

# read demand data
for scen_short, scen_long, in EU_policy_spaced_dict.items():
    scen_long_no_space = scen_long.replace(" ", "")
    for run_year in run_year_list:
        for climate_year in climate_years_list:
            # demand data -------------------------------------------------------------------------------
            df_dem = pd.read_csv(input_dir + "demandComponentsAnnual_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=0)
            # add columnn node

            # add columns for scenario, zone, zone_long, tech, weather_year
            df_dem["scenario"] = scen_long_no_space
            df_dem["run_year"] = run_year
            df_dem["weather_year"] = climate_year

            # add a column "node", which is equal to the index of df_dem, but with 00 at the end if the size of the index' length is 2
            df_dem["node"] = df_dem.index
            df_dem["node"] = df_dem["node"].apply(lambda x: x + "00" if len(x) == 2 else x)

            # add a column "plant_name", which is equal to the index of df_dem, but with 00 at the end if the size of the index' length is 2
            df_dem["plant_name"] = df_dem.index
            df_dem["plant_name"] = df_dem["plant_name"].apply(lambda x: x + "00_electrolyzer" if len(x) == 2 else x+ "_electrolyzer")

            # add a column that is equal to sum of columns_electrolyzer
            df_dem["electrolyzer"] = 1000 * df_dem[columns_electrolyzer].sum(axis=1)

            # add a column that is equal to sum of columns_basedemand, the conventional demand
            df_dem["demand"] = 1000 * df_dem[columns_basedemand].sum(axis=1)

            # merge df_dem with demand_all_df based on index, add columns from df_dem to demand_all_df
            demand_all_df = pd.concat([demand_all_df, df_dem])

# export demand data ---------------------
# export electrolyzer_net_demand data
# export the dataframe, only columns plant_name scenario run_year weather_year sum_electrolyzer, and pivot run_year to columns
demand_all_df.pivot_table(index=["plant_name", "node", "scenario", "weather_year"], columns="run_year", values="electrolyzer", aggfunc="sum").to_csv(target_output_dir + "electrolyzer_net_demand.csv")

# export conventional demand
# # export the dataframe, only columns plant_name scenario run_year weather_year sum_electrolyzer, and pivot run_year to columns
demand_all_df.pivot_table(index=["node", "scenario", "weather_year"], columns="run_year", values="demand", aggfunc="sum").to_csv(target_output_dir + "demand.csv")


# create plants_electrolyzer.csv ----------------------------------------------------------------------------
plants_electrolyzer_list_df = pd.DataFrame(columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])

plants_electrolyzer_list_df["index"] = demand_all_df["plant_name"]
plants_electrolyzer_list_df["node"] = demand_all_df["node"]
plants_electrolyzer_list_df["market"] = demand_all_df["node"]
plants_electrolyzer_list_df["plant_type"] = "electrolyzer"
plants_electrolyzer_list_df["tech"] = "electrolyzer"

# remove duplicates from plants_electrolyzer_list_df (duplicates results from the fact that the same plant is in the same country for different weather years)
plants_electrolyzer_list_df = plants_electrolyzer_list_df.drop_duplicates()

plants_electrolyzer_list_df.to_csv(target_output_dir + "plants_electrolyzer.csv", encoding="utf-8", index=False)

# %%
#%% every thing below is deactivated, because the method didnt'make sense anymore
# demand_all_df = pd.DataFrame()

# # read demand data
# for scen_short, scen_long, in EU_policy_spaced_dict.items():
#     scen_long_no_space = scen_long.replace(" ", "")
#     for run_year in run_year_list:
#         for climate_year in climate_years_list:
#             # demand data -------------------------------------------------------------------------------
#             df_dem = pd.read_csv(input_dir + "demandComponentsAnnual_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0,])

#             # add columns for scenario, zone, zone_long, tech, weather_year
#             df_dem["scenario"] = scen_long_no_space
#             df_dem["run_year"] = run_year
#             df_dem["weather_year"] = climate_year
#             # add a column that is equal to sum of columns_electrolyzer
#             df_dem["sum_electrolyzer"] = df_dem[columns_electrolyzer].sum(axis=1)

#             # merge df_dem with demand_all_df based on index, add columns from df_dem to demand_all_df
#             demand_all_df = pd.concat([demand_all_df, df_dem])


# # read import_export data
# exportsH2Sum_df = pd.DataFrame()

# for scen_short, scen_long, in EU_policy_spaced_dict.items():
#     scen_long_no_space = scen_long.replace(" ", "")
#     for run_year in run_year_list:
#         for climate_year in climate_years_list:
#             # demand data ------------------------------
#             df_H2 = pd.read_csv(input_dir + "exportsH2Sum_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0,])

#             # add columns for scenario, zone, zone_long, tech, weather_year
#             df_H2["scenario"] = scen_long_no_space
#             df_H2["run_year"] = run_year
#             df_H2["weather_year"] = climate_year

#             exportsH2Sum_df = pd.concat([exportsH2Sum_df, df_H2])
# #rename column sum to net_export
# exportsH2Sum_df = exportsH2Sum_df.rename(columns={"sum": "net_export"})

# # calculate net demand for each country ---------------------------
# # merge exportsH2Sum_df and demand_all_df[scenario,run_year,sum_electrolyzer] based on index, scenario and run_year
# # demand_electrolyzer_df is equal to demand_all_df[scenario,run_year,sum_electrolyzer]
# demand_electrolyzer_df = demand_all_df[["scenario", "run_year", "weather_year", "sum_electrolyzer"]]

# # set index and columns of demand_electrolyzer_df as index, except for sum_electrolyzer
# demand_electrolyzer_df2 = demand_electrolyzer_df.reset_index()
# demand_electrolyzer_df2 = demand_electrolyzer_df2.set_index(["index", "scenario", "run_year", "weather_year"])


# exportsH2Sum_df2 = exportsH2Sum_df.reset_index()
# exportsH2Sum_df2 = exportsH2Sum_df2.set_index(["index", "scenario", "run_year", "weather_year"])


# dem_exp_df = pd.merge(exportsH2Sum_df2, demand_electrolyzer_df2, left_index=True, right_index=True)

# dem_exp_df.reset_index(inplace=True)

# dem_exp_df["tech"] = "electrolyzer"

# dem_exp_df["net_demand"] = dem_exp_df["sum_electrolyzer"] + dem_exp_df["net_export"]

# # dem_exp_df["node"] is equal to dem_exp_df.loc[:, "index"] + "00" if is of size 2, else it is equal to dem_exp_df.loc[:, "index"]
# # if size is 2, it is a country code and needs 00, if size is 4, it is a region code already
# dem_exp_df["node"] = dem_exp_df["index"].apply(lambda x: x + "00" if len(x) == 2 else x)

# dem_exp_df["name"] = "electrolyzer_" + dem_exp_df["node"]

# # export the columns name, node, tech, scenario, run_year, weather_year, electrolyzer_net_demand
# dem_exp_df = dem_exp_df[["name", "node", "tech", "scenario", "run_year", "weather_year", "net_demand"]]