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

            # add columns for scenario, zone, zone_long, tech, weather_year
            df_gen["scenario"] = scen_long_no_space
            df_gen["weather_year"] = climate_year
            df_gen["run_year"] = run_year

            # merge df_gen with generation_all_df based on index, add columns from df_gen to generation_all_df
            generation_all_df = pd.concat([generation_all_df, df_gen])

        # ---------------------------------------------------------------------------------------------
        # capacity data -------------------------------------------------------------------------------
        df_cap = pd.read_csv(input_dir + "capacity_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0, 1, 2])

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

plants_list.to_csv(target_output_dir + "plants_non_hydro.csv", encoding="utf-8", index=False)



# export capacity_conv_ordered_df---------------------------------------------------------------------
# pivot and aggregate the data
capacity_conv_ordered_df = capacity_conv_ordered_df.pivot_table(index=['node', 'name', 'scenario'], #TODO order
                                                    columns='run_year', 
                                                    values='capacity',
                                                    aggfunc='sum').reset_index()

# remove the column node
capacity_conv_ordered_df = capacity_conv_ordered_df.drop(columns="node")

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
            df_dem = pd.read_csv(input_dir + "demandComponentsAnnual_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0,])

            # add columns for scenario, zone, zone_long, tech, weather_year
            df_dem["scenario"] = scen_long_no_space
            df_dem["run_year"] = run_year
            df_dem["weather_year"] = climate_year
            # add a column that is equal to sum of columns_electrolyzer
            df_dem["sum_electrolyzer"] = df_dem[columns_electrolyzer].sum(axis=1)

            # merge df_dem with demand_all_df based on index, add columns from df_dem to demand_all_df
            demand_all_df = pd.concat([demand_all_df, df_dem])


# read import_export data
exportsH2Sum_df = pd.DataFrame()

for scen_short, scen_long, in EU_policy_spaced_dict.items():
    scen_long_no_space = scen_long.replace(" ", "")
    for run_year in run_year_list:
        for climate_year in climate_years_list:
            # demand data ------------------------------
            df_H2 = pd.read_csv(input_dir + "exportsH2Sum_" + scen_long_no_space + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index_col=[0,])

            # add columns for scenario, zone, zone_long, tech, weather_year
            df_H2["scenario"] = scen_long_no_space
            df_H2["run_year"] = run_year
            df_H2["weather_year"] = climate_year

            exportsH2Sum_df = pd.concat([exportsH2Sum_df, df_H2])
#rename column sum to net_export
exportsH2Sum_df = exportsH2Sum_df.rename(columns={"sum": "net_export"})

# calculate net demand for each country ---------------------------
# merge exportsH2Sum_df and demand_all_df[scenario,run_year,sum_electrolyzer] based on index, scenario and run_year
# demand_electrolyzer_df is equal to demand_all_df[scenario,run_year,sum_electrolyzer]
demand_electrolyzer_df = demand_all_df[["scenario", "run_year", "weather_year", "sum_electrolyzer"]]

# set index and columns of demand_electrolyzer_df as index, except for sum_electrolyzer
demand_electrolyzer_df2 = demand_electrolyzer_df.reset_index()
demand_electrolyzer_df2 = demand_electrolyzer_df2.set_index(["index", "scenario", "run_year", "weather_year"])


exportsH2Sum_df2 = exportsH2Sum_df.reset_index()
exportsH2Sum_df2 = exportsH2Sum_df2.set_index(["index", "scenario", "run_year", "weather_year"])


dem_exp_df = pd.merge(exportsH2Sum_df2, demand_electrolyzer_df2, left_index=True, right_index=True)

dem_exp_df.reset_index(inplace=True)

dem_exp_df["tech"] = "electrolyzer"

dem_exp_df["net_demand"] = dem_exp_df["sum_electrolyzer"] + dem_exp_df["net_export"]

dem_exp_df["node"] = dem_exp_df.loc[:, "index"] + "00"

dem_exp_df["name"] = "electrolyzer_" + dem_exp_df["node"]

# export the columns name, node, tech, scenario, run_year, weather_year, electrolyzer_net_demand
dem_exp_df = dem_exp_df[["name", "node", "tech", "scenario", "run_year", "weather_year", "electrolyzer_net_demand"]]
dem_exp_df.to_csv(target_output_dir + "z.csv", encoding="utf-8", index=False)

# create plants_electrolyzer.csv ----------------------------------------------------------------------------
plants_electrolyzer_list_df = pd.DataFrame(columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])

plants_electrolyzer_list_df["index"] = dem_exp_df["name"]
plants_electrolyzer_list_df["node"] = dem_exp_df["node"]
plants_electrolyzer_list_df["market"] = dem_exp_df["node"]
plants_electrolyzer_list_df["plant_type"] = "electrolyzer"
plants_electrolyzer_list_df["tech"] = "electrolyzer"

plants_electrolyzer_list_df.to_csv(target_output_dir + "plants_electrolyzer.csv", encoding="utf-8", index=False)



# %%
