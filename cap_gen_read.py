import pandas as pd
import os
import glob
import logging

# define paths ---------------------------------------------------------------
source_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\TYNDP_2022//"
target_output_dir = r"capacit_gen//"

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


# # # functions      -----------------------------------------------------------
# def read_data_cap_gen(EU_policy, run_year, climate_year):
#     """
#     """
#     # target xlsx file
#     file_name = source_data_dir + r"\220310_Updated_Electricity_Modelling_Results.xlsx"
#     df_all = pd.read_excel(file_name, sheet_name="Capacity & Dispatch")

#     # for the values in the column "Climate Year", reomve "CY "
#     df_all["Climate Year"] = df_all["Climate Year"].str.replace("CY ", "")


#     # keep the part of the df_all that corresponds to the run_year and EU_policy
#     df_selected = df_all[(df_all["Scenario"] == EU_policy)
#                          & (df_all["Year"] == run_year)
#                          & (df_all["Climate Year"] == str(climate_year))
#                         ]

#     # drop the columns that consist of only NaNs
#     df_selected = df_selected.dropna(axis=1, how="all")

#     # create a list of all lines
#     node_list = df_selected["Node"].unique().tolist()
#     nodeline_list = df_selected["Node/Line"].unique().tolist()
#     fuel_list = df_selected["Fuel"].unique().tolist()


#     # loop over sheets to read in the data
#     multi_index = pd.MultiIndex(levels=[[], [], []], codes=[[], [], []], names=['node', 'nodeline', 'fuel'])
#     generation_all_df = pd.DataFrame(columns=['generation'], index=multi_index)
#     capacity_all_df = pd.DataFrame(columns=['capacity'], index=multi_index)

#     # lists to store not fully defined lines
#     genertaion_missing_fuel = []
#     capacity_missing_fuel = []

#     for node in node_list:
#         for nodeline in nodeline_list:
#             for fuel in fuel_list:
#                 # find the corresponding value for generation in node nodeline and fuel in the df_selected
#                 gen_temp_df = df_selected[(df_selected["Node"] == node) 
#                                     & (df_selected["Node/Line"] == nodeline)
#                                     & (df_selected["Fuel"] == fuel)
#                                     & (df_selected["Parameter"] == "Dispatch (GWh)")
#                                     ]
                
#                 if gen_temp_df.shape[0] == 1:
#                     # to generation_all_df, add a row with index (node, nodeline, fuel) and column "generation"
#                     generation_all_df.loc[(node, nodeline, fuel), "generation"] = gen_temp_df["Value"].values[0]
#                     # # if line does not include any of the elements in elements_excluded, add it to the export_selected_df
#                     # if not any(ele in line for ele in elements_excluded):
#                     #     export_selected_df.loc[line, "Export Capacity (MW)"] = temp_df["Value"].values[0]
#                 elif gen_temp_df.shape[0] == 0:
#                     genertaion_missing_fuel.append((node, nodeline, fuel))
#                 elif gen_temp_df.shape[0] > 1:
#                     logging.warning(f"Multiple values for generation for node {node}, nodeline {nodeline}, fuel {fuel}")

#                 # find the corresponding value for capacity in node nodeline and fuel in the df_selected
#                 cap_temp_df = df_selected[(df_selected["Node"] == node) 
#                                     & (df_selected["Node/Line"] == nodeline)
#                                     & (df_selected["Fuel"] == fuel)
#                                     & (df_selected["Parameter"] == "Capacity (MW)")
#                                     ]
                
#                 if cap_temp_df.shape[0] == 1:
#                     # to capacity_all_df, add a row with index (node, nodeline, fuel) and column "capacity"
#                     capacity_all_df.loc[(node, nodeline, fuel), "capacity"] = cap_temp_df["Value"].values[0]
#                     # # if line does not include any of the elements in elements_excluded, add it to the export_selected_df
#                     # if not any(ele in line for ele in elements_excluded):
#                     #     export_selected_df.loc[line, "Export Capacity (MW)"] = temp_df["Value"].values[0]
#                 elif cap_temp_df.shape[0] == 0:
#                     capacity_missing_fuel.append((node, nodeline, fuel))
#                 elif cap_temp_df.shape[0] > 1:
#                     logging.warning(f"Multiple values for capacity for node {node}, nodeline {nodeline}, fuel {fuel}")

#     return generation_all_df, capacity_all_df



# # read in the data and write to csvs ----------------------------------------------------------
# # if target_output_dir does not exist, create it
# if not os.path.exists(target_output_dir):
#     os.makedirs(target_output_dir)

# for run_year in PECD_data_years_list:
#     for EU_policy, EU_policy_long in EU_policy_spaced_dict.items():
#         for climate_year in climate_years_list:
#             print("Reading generation and capacity data for ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy, 90*"-")
#             generation_all_df, capacity_all_df = read_data_cap_gen(EU_policy_long, run_year, climate_year)
#             # write the data to csv file
#             EU_policy_no_spaces = EU_policy_dict[EU_policy]
#             generation_all_df.to_csv(target_output_dir + "generation_" + EU_policy_no_spaces + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
#             capacity_all_df.to_csv(target_output_dir + "capacity_" + EU_policy_no_spaces + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)            

# sanity checks -----------------------------------------------
# read all export_import_selected_df files and write to one file
# find all files in the target_output_dir that start with "NTC_export_import_selected_"
os.chdir(target_output_dir)
extension = 'csv'
for element in ["generation", "capacity"]:
    all_filenames = [i for i in glob.glob(element+'_*.{}'.format(extension))]

    # loop over all files, read them in and write to one file
    all_df = pd.DataFrame()
    for file in all_filenames:
        scen_name = file.split("_")[1]
        run_year = file.split("_")[3].split(".")[0]


        # read in the file
        df = pd.read_csv(file, index_col=[0, 1, 2])

        # add scenario and run_year to the column names
        df = df.add_prefix(scen_name + "_" + run_year + "_")

        all_df = pd.concat([all_df, df], axis=1)

    all_df.to_csv("aggregated_"+ element + ".csv", index=True)
