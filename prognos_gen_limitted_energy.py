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

dict_tech_prognos_reverse = defaultdict(list)
for k, v in dict_tech_prognos.items():
    dict_tech_prognos_reverse[v].append(k)

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
annual_gen = pd.DataFrame(columns=["zone", "scenario", "tech", "weather_year"] + run_year_list)
annual_gen.set_index(["zone", "scenario", "tech", "weather_year"] , inplace=True)

for scenario in ch_scenario_list:
    file_dir = f"{source_data_dir}EP2050+_Szenarienergebnisse_{ch_scenario_list_subs_name[scenario]}//"
    file_name = f"EP2050+_Umwandlungssynthese_2020-2060_{ch_scenario_list_subs_name2[scenario]}_2022-04-12.xlsx"
    gen_df = pd.read_excel(file_dir + file_name, sheet_name="02 Stromerzeugung", header=38, index_col=1)
    for run_year in run_year_list:
        for tech in ["other", "biomass",]:
            # sum up all values with index equal to dict_tech_prognos_reverse[tech] and run_year
            print(gen_df.loc[gen_df.index.isin(dict_tech_prognos_reverse[tech]), run_year])
            annual_gen.loc[("CH00", scenario, tech, "all"), run_year] = gen_df.loc[gen_df.index.isin(dict_tech_prognos_reverse[tech]), run_year].sum() * 1000 * 1000

annual_gen.to_csv(os.path.join(target_output_dir, "generation_CH.csv"))