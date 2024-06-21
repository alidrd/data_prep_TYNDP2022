import pandas as pd
import os
from collections import defaultdict
import numpy as np


# define paths ---------------------------------------------------------------
source_data_dir = r"C:/Users\daru/OneDrive - ZHAW/EDGE\data_sources/Energieperskpektiven2050+//"
target_output_dir  = r"inputs_to_model//"
# define years ---------------------------------------------------------------
run_year_list = [2030, 2040 , 2050]
climate_year_list = [1995, 2008, 2009]
ch_scenario_list = ["WWB", "ZEROBasis", "ZEROvarA", "ZEROvarB"]

ch_target_regions = ["CH0"+str(i) for i in range(1, 8)]

ch_scenario_list_subs_name = {
    "WWB": "WWB",
    "ZEROBasis": "ZERO-Basis",
    "ZEROvarA": "ZERO-A",
    "ZEROvarB": "ZERO-B",
}

ch_scenario_list_subs_name2 = {
    "WWB": "WWB_KKW60_aktuelleRahmenbedingungen",
    "ZEROBasis": "ZERO Basis_KKW60_ausgeglicheneJahresbilanz",
    "ZEROvarA": "ZERO-A_KKW60_ausgeglicheneJahresbilanz",
    "ZEROvarB": "ZERO-B_KKW60_ausgeglicheneJahresbilanz",
}

# read demand data -----------------------------------------------------------
# annual demand, defined as total demand minus electrolyzer demand
annual_demand = pd.DataFrame(columns=["node", "scenario"] + run_year_list)
annual_demand.set_index(["node", "scenario"], inplace=True)

for scenario in ch_scenario_list:
    file_dir = f"{source_data_dir}EP2050+_Szenarienergebnisse_{ch_scenario_list_subs_name[scenario]}//"
    file_name = f"EP2050+_Umwandlungssynthese_2020-2060_{ch_scenario_list_subs_name2[scenario]}_2022-04-12.xlsx"
    demand_df = pd.read_excel(file_dir + file_name, sheet_name="01 Stromverbrauch", header=10, index_col=1)
    for run_year in run_year_list:
        annual_demand.loc[("CH00", scenario), run_year] = (demand_df.loc["Landesverbrauch", run_year] - \
                                                                           demand_df.loc["Elektrolyse", run_year]) * 1000 * 1000
annual_demand.to_csv(os.path.join(target_output_dir, "annual_demand_CH.csv"))
# electrlyzer demand -------------------------------------------------------------------
electrolyzer_net_demand = pd.DataFrame(columns=["plant_name", "node", "scenario", "run_year", "net_demand"])
electrolyzer_net_demand.set_index(["plant_name", "node", "scenario", "run_year"], inplace=True)
# "name", "node", "tech", "scenario", "run_year", "weather_year", "net_demand"]
electrolyzer_capacities = pd.DataFrame(columns=["plant_name", "scenario"] + run_year_list)
electrolyzer_capacities.set_index(["plant_name", "scenario"], inplace=True)

plant_name = "CH00_electrolyzer"

# read electrolyzer data ------------------------------------------------------
for scenario in ch_scenario_list:
    file_dir = f"{source_data_dir}EP2050+_Szenarienergebnisse_{ch_scenario_list_subs_name[scenario]}//"
    file_name = f"EP2050+_Umwandlungssynthese_2020-2060_{ch_scenario_list_subs_name2[scenario]}_2022-04-12.xlsx"
    electrlyzer_data_df = pd.read_excel(file_dir + file_name, sheet_name="08 PtX", header=10, index_col=1)
    for run_year in run_year_list:
        electrolyzer_net_demand.loc[(plant_name, "CH00", scenario, run_year), "net_demand"] = 1000000 * electrlyzer_data_df.loc["Stromverbrauch Elektrolyseure", run_year]
        electrolyzer_capacities.loc[(plant_name, scenario), run_year] = 1000 * electrlyzer_data_df.loc["Installierte Leistung Elektrolyseure", run_year]
# final adjustments to the dataframe and export --------------------------------
# add repeated columns
electrolyzer_net_demand.reset_index(inplace=True)
electrolyzer_net_demand["weather_year"] = "all"
# reorder columns based on ["name", "node", "tech", "scenario", "run_year", "weather_year", "net_demand"]
electrolyzer_net_demand = electrolyzer_net_demand[["plant_name", "node", "scenario", "run_year", "weather_year", "net_demand"]]
# pivot table for run_year
electrolyzer_net_demand = electrolyzer_net_demand.pivot_table(index=["plant_name", "scenario", "weather_year"], columns="run_year", values="net_demand")

# export
electrolyzer_net_demand.to_csv(os.path.join(target_output_dir, "electrolyzer_net_demand_CH.csv"))



electrolyzer_capacities.to_csv(os.path.join(target_output_dir, "electrolyzer_capacities_CH.csv"))
# electrolyzer plants ---------------------------------------------------------
# only one plant in CH00
plants_electrolyzer = pd.DataFrame(columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])
plants_electrolyzer.loc[0] = [plant_name, "CH00", "CH00", "electrolyzer", "electrolyzer", "" , "", "", "", ""]
plants_electrolyzer.to_csv(os.path.join(target_output_dir, "plants_electrolyzer_CH00.csv"), index=False)

# one plant per region ch_target_regions
plants_electrolyzer = pd.DataFrame(index=ch_target_regions, columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])

row_counter = 0
for node in ch_target_regions:
    plants_electrolyzer.loc[node,:] = ["electrolyzer_" + node, node, "CH00", "electrolyzer", "electrolyzer", "" , "", "", "", ""] 
    row_counter += 1

plants_electrolyzer.to_csv(os.path.join(target_output_dir, "plants_electrolyzer_CH01_CH07.csv"), index=False)