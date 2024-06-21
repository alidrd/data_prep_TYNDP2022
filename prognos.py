import pandas as pd
import os
from collections import defaultdict
import numpy as np

# define paths ---------------------------------------------------------------
source_data_dir = r"C:/Users\daru/OneDrive - ZHAW/EDGE\data_sources/Prognos/Used_data_for_analysis//"
target_output_dir  = r"inputs_to_model//"
# define years ---------------------------------------------------------------
run_year_list = [2030, 2040 , 2050]
climate_year_list = [1995, 2008, 2009]
ch_scenario_list = ["WWB", "ZEROBasis", "ZEROvarA", "ZEROvarB"]

ch_target_regions = ["CH0"+str(i) for i in range(1, 8)]

ch_scenario_list_subs_name = {
    "WWB": "WWB",
    "ZEROBasis": "ZEROBasis",
    "ZEROvarA": "ZEROVarA",
    "ZEROvarB": "ZEROVarB",
}
dict_tech_prognos = {
    'ARA' : 'other',
    'Biogas' : 'biomass',              # this is turned into other so that it is treated as infeed technology
    'biomasse (Holz)' : 'biomass', # this is turned into other so that it is treated as limited energy technology
    'Biomasse (Holz)' : 'biomass', # this is turned into other so that it is treated as limited energy technology
    'biomasse-Holz' :  'biomass',  # added due to different naming in prognos files
    'Biomasse-Holz' :  'biomass',  # added due to different naming in prognos files
    'Fossile' : 'gas',
    'Geothermie' : 'other',        # this is turned into other so that it is treated as infeed
    'KVA' : 'other',
    'KVA (EE-Anteil)' : 'other',
    'KVA-Erneuerbar' : 'other',
    'Kernkraft' : 'nuclear',
    # 'Laufwasserkraft' : 'RoR',
    'PV' : 'pvrf',                # newly added
    # 'PV-Bat': 'pvrf',             # newly added - rooftop pv
    'Dezentrale Batterien': "battery",
    # 'Pumpspeicher' : 'pumped_open',
    # 'Pumpspeicherwasser' : 'pumped_open',    # added due to different naming in prognos files
    # 'Speicherwasser' : 'dam',
    'Windenergie' : 'windon',    
    'Windkraft' : 'windon',                 # added due to different naming in prognos files
}


# tech_names_in_model are equal to the unique values of dict_tech_prognos
tech_names_in_model = list(set(dict_tech_prognos.values()))

# dict_tech_prognos_reverse has the keys and values of dict_tech_prognos reversed, consider that the values of dict_tech_prognos are not unique

dict_tech_prognos_reverse = defaultdict(list)
for k, v in dict_tech_prognos.items():
    dict_tech_prognos_reverse[v].append(k)
dict_tech_prognos_reverse["other"]


#%% read generation capacity data

# read files
capacities_dict = {}

for scenario in ch_scenario_list:
    file_name = source_data_dir + "EPCH-" + scenario + "//Struktur//Erzeugungsleistung---" + scenario + ".xlsx"
    file_name_v2 = source_data_dir + "EPCH-" + scenario + "//Struktur//Erzeugungsleistung---" + ch_scenario_list_subs_name[scenario] + ".xlsx"
    file_name_v3 = source_data_dir + "EPCH-" + ch_scenario_list_subs_name[scenario] + "//Struktur//Erzeugungsleistung---" + ch_scenario_list_subs_name[scenario] + ".xlsx"
    file_name_v4 = source_data_dir + "2021-08-19 Regionale Kapazitäten Erzeugung//leistung_regional.xlsx"
    if os.path.isfile(file_name):
        capacities_dict[scenario] = pd.read_excel(file_name)
    elif os.path.isfile(file_name_v2):
        capacities_dict[scenario] = pd.read_excel(file_name_v2)
    elif os.path.isfile(file_name_v3):
        capacities_dict[scenario] = pd.read_excel(file_name_v3)
    elif os.path.isfile(file_name_v4):
        #EPCH-ZEROBasis had no file in its folder, instead file_name_v4 is used
        capacities_dict[scenario] = pd.read_excel(file_name_v4).rename(columns={"leistung": "leistung / GW"})
    else:    
        print("File not found: ", file_name)

capacities_pv_batteries = pd.read_excel(source_data_dir + "2022-03-22 Corrected Battery data//Erzeugungsleistung_korrigiert.xlsx")
print("imported scenarios: ")
print(capacities_dict.keys())

#%% creating the dataframes for generation capacities
nonhydro_capacities_gen_df = pd.DataFrame(columns=['name', 'scenario'] + run_year_list)
nonhydro_capacities_gen_df.set_index(['name', 'scenario'], inplace=True)

#NOTE read batteries from C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\Prognos\2022-03-22 Corrected Battery data

for tech in tech_names_in_model: 
    # for pv and batteries, Erzeugungsleistung_korrigierts.xlsx is used
    if tech not in ["pvrf", "pvnu", "windon", "battery"]:
        for region in ch_target_regions:
            plant_name = region + "_" + tech
            for run_year in run_year_list:           
                for scenario in ch_scenario_list:
                    # capacity is equal to all values in capacities_dict[scenario] if column typ is equal to tech and region is equal to region and year is equal to run_year
                    try:
                        capacity = capacities_dict[scenario][
                            capacities_dict[scenario]['typ'].isin(dict_tech_prognos_reverse[tech])
                            & (capacities_dict[scenario]["region"] == region) 
                            & (capacities_dict[scenario]["jahr"] == run_year)]["leistung / GW"].sum() * 1000
                    except IndexError:
                        capacity = np.nan
                    # add a row to nonhydro_capacities_gen_df with the index (plant_name, scenario) and add value capacity to column run_year
                    nonhydro_capacities_gen_df.loc[(plant_name, scenario), run_year] = capacity
    elif tech in ["battery",]:
        for region in ch_target_regions:
            plant_name = region + "_" + tech
            for run_year in run_year_list:
                for scenario in ch_scenario_list:
                    capacity = capacities_pv_batteries[
                        capacities_pv_batteries["typ"].isin(dict_tech_prognos_reverse[tech])
                        & (capacities_pv_batteries["region"] == region)
                        & (capacities_pv_batteries["jahr"] == run_year)
                        & (capacities_pv_batteries["szen"] == ch_scenario_list_subs_name[scenario])
                        ]["leistung / GW"].sum() * 1000
                    nonhydro_capacities_gen_df.loc[(plant_name, scenario), run_year] = capacity

# keep the plants that have non-zero capacities in at least one year/scenario
for plants in nonhydro_capacities_gen_df.index.get_level_values("name").unique():
    if nonhydro_capacities_gen_df.loc[plants].sum().sum() == 0:
        nonhydro_capacities_gen_df.drop(index=plants, inplace=True)

# export the dataframe to a csv file
nonhydro_capacities_gen_df.to_csv(f"{target_output_dir}//nonhydro_capacities_gen_CH.csv", index=True)

# -------------------------------------------------------------------------------------------
# RES plants
nonhydro_capacities_gen_res_df = pd.DataFrame(columns=['name', 'node', 'tech', 'scenario', ] + run_year_list)
nonhydro_capacities_gen_res_df.set_index(['name', 'node', 'tech', 'scenario', ], inplace=True)


for tech in ["windon", "pvrf", "pvnu"]: 
    # for pv and batteries, Erzeugungsleistung_korrigierts.xlsx is used
    if tech in [ "windon",]:
        for region in ch_target_regions:
            plant_name = region + "_" + tech
            for run_year in run_year_list:           
                for scenario in ch_scenario_list:
                    # capacity is equal to all values in capacities_dict[scenario] if column typ is equal to tech and region is equal to region and year is equal to run_year
                    try:
                        capacity = capacities_dict[scenario][
                            capacities_dict[scenario]['typ'].isin(dict_tech_prognos_reverse[tech])
                            & (capacities_dict[scenario]["region"] == region) 
                            & (capacities_dict[scenario]["jahr"] == run_year)]["leistung / GW"].sum() * 1000
                    except IndexError:
                        capacity = np.nan
                    # add a row to nonhydro_capacities_gen_df with the index (plant_name, scenario) and add value capacity to column run_year
                    nonhydro_capacities_gen_res_df.loc[(plant_name, region, tech, scenario), run_year] = capacity
    elif tech in ["pvrf", "pvnu",]:
        for region in ch_target_regions:
            plant_name = region + "_" + tech
            for run_year in run_year_list:
                for scenario in ch_scenario_list:
                    capacity = capacities_pv_batteries[
                        capacities_pv_batteries["typ"].isin(dict_tech_prognos_reverse[tech])
                        & (capacities_pv_batteries["region"] == region)
                        & (capacities_pv_batteries["jahr"] == run_year)
                        & (capacities_pv_batteries["szen"] == ch_scenario_list_subs_name[scenario])
                        ]["leistung / GW"].sum() * 1000
                    nonhydro_capacities_gen_res_df.loc[(plant_name, region, tech, scenario), run_year] = capacity


# keep the plants that have non-zero capacities in at least one year/scenario
for plants in nonhydro_capacities_gen_res_df.index.get_level_values("name").unique():
    if nonhydro_capacities_gen_res_df.loc[plants].sum().sum() == 0:
        nonhydro_capacities_gen_res_df.drop(index=plants, inplace=True)

# export the dataframe to a csv file
nonhydro_capacities_gen_res_df.to_csv(f"{target_output_dir}//res_capacities_CH.csv", index=True)

#%% create plant list

plants_list = pd.DataFrame(columns=["index", "node", "market", "plant_type", "tech", "upperwn", "lowerwn", "eta", "eta_pump", "n_redispatch"])

plant_name_list = nonhydro_capacities_gen_df.index.get_level_values("name").unique()
for plant_name in plant_name_list:
    tech = plant_name.split("_")[-1]
    region = plant_name.split("_")[0]
    plants_list.loc[plant_name, "index"] = plant_name
    plants_list.loc[plant_name, "node"] = "CH00"
    plants_list.loc[plant_name, "market"] = "CH00"
    if tech in ['nuclear', 'other', 'biomass', 'battery', 'gas']:
        plants_list.loc[plant_name, "plant_type"] = "Conventional"
    
    elif tech in ['pumped_open', 'dam', 'RoR']:
        plants_list.loc[plant_name, "plant_type"] = "Hydro"
    else:
        plants_list.loc[plant_name, "plant_type"] = "RES"


    plants_list.loc[plant_name, "tech"] = tech
    plants_list.loc[plant_name, "upperwn"] = ""
    plants_list.loc[plant_name, "lowerwn"] = ""
    plants_list.loc[plant_name, "eta"] = ""
    plants_list.loc[plant_name, "eta_pump"] = ""
    plants_list.loc[plant_name, "n_redispatch"] = ""

plants_list.to_csv(f"{target_output_dir}plants_non_hydro_CH.csv", index=False)