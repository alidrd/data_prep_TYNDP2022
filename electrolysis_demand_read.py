"""
Reads the demand components, including     
    "Electrolysis Config 1" ,
    "Electrolysis Config 2" ,
    "Electrolysis Config 3" ,
    "Electrolysis Config 4" , 
from the TYNDP 2022 data set and saves them as csv file.
"""	

import pandas as pd
import mappings_tyndp as mp
import os

target_output_dir = r"annuals_cap_dem_gen_imp//"



# define years ---------------------------------------------------------------
# years for which capacity factor is available
run_year_list = [2050, 2040, 2030] # 2030, 2025, 2040

# target climate years
climate_years_list = [2008, 2009, 1995]

# policy scenario
EU_policy_spaced_dict = {
    "DE": "Distributed Energy" ,
    "GA": "Global Ambition",
    }

# target_scenario = "Global Ambition"  #Distributed Energy  #Global Ambition
# target_climate_year = 1995
# target_year = 2050

target_country_list = [
    "RU",
    "MA",
    "CZ",
    "FR",
    "DE",
    "NO",
    "ES",
    "IT",
    "TR",
    "DK",
    "BG",
    "SE",
    "FI",
    "BE",
    "AT",
    "PT",
    "GR",
    "PL",
    "HU",
    "CH",
    "NL",
    "EE",
    "UK",
    "IE",
    "LT",
    "RO",
    "HR",
    "LV",
    "SK",
    "SI",
    ]

# read data -------------------------------------------------------------------
demand_all_df = pd.read_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\220310_Updated_Electricity_Modelling_Results.xlsx", sheet_name="Demand")

# select scenario and year
# demand_scen_year_clim_df = demand_all_df[(demand_all_df["Scenario"] == target_scenario) & 
#                                          (demand_all_df["Year"] == target_year)]

if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)


demand_compontents = [
    "Transmission Node" ,
    "Transport Node" ,
    "Electrolysis Config 1" ,
    "Electrolysis Config 2" ,
    "Electrolysis Config 3" ,
    "Electrolysis Config 4" ,
    "Prosumer Node" ,
]

demand_components_annual_df = pd.DataFrame(columns=demand_compontents, index=target_country_list)

for run_year in run_year_list:
    print(f"reading run_year: {run_year}")
    for climate_year in climate_years_list:
        for scne_shorts, scen_long_spaced in EU_policy_spaced_dict.items():
            demand_components_annual_df = pd.DataFrame(columns=demand_compontents, index=target_country_list)
            for target_country in target_country_list:
                for demand_component in demand_compontents:
                    try: 
                        demand_components_annual_df.loc[target_country, demand_component] = demand_all_df[(demand_all_df["Node"].str.startswith(target_country)) & 
                                                                                                        (demand_all_df["Type_node"] == demand_component) &
                                                                                                        (demand_all_df["Climate Year"] == "CY " + str(climate_year)) &
                                                                                                        (demand_all_df["Year"] == run_year) &
                                                                                                        (demand_all_df["Scenario"] == scen_long_spaced)
                                                                                                        ]["Value"].values[0]
                    except IndexError:
                        demand_components_annual_df.loc[target_country, demand_component] = 0

                # demand_components_annual_df.to_csv(r"capacit_gen//demand_components_annual.{}.csv")
                demand_components_annual_df.to_csv(target_output_dir + "demandComponentsAnnual_" + scen_long_spaced.replace(" ", "") + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)            