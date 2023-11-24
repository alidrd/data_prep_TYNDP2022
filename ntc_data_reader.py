import pandas as pd
import logging	# for logging
import os	    # for changing the working directory
import glob


# define paths ---------------------------------------------------------------
climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\TYNDP_2022//"
target_output_dir = r"NTC//"

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

# Mappings of zones in the model 
Mapping_zone_country = {}
# read values in market_nodes.csv into a dictionary, where the key is data_granularity and the value is the country, using pandas
df = pd.read_csv("market_nodes.csv")
for index, row in df.iterrows():
    Mapping_zone_country[row["data_granularity"]] = row["country"]

elements_excluded = ["EV2", "H2MT", "SNR1", "H2R1", "RETE"]

# # functions      -----------------------------------------------------------
def read_data_NTC(EU_policy, run_year, climate_year):
    """
    Read in the data from the PECD file for the given technology, PECD year and climate year.
    The data is read from the sheet with the name of the country in the model.
    The data is read from the column with the name of the climate year.
    The data is renamed to the name of the country in the model.
    The index is renamed to "t_" + the row number.
    The data is returned as a dataframe.
    """
    # target xlsx file
    file_name = climate_data_dir + r"\220310_Updated_Electricity_Modelling_Results.xlsx"
    df_all = pd.read_excel(file_name, sheet_name="Line")

    # keep the part of the df_all that corresponds to the run_year and EU_policy
    df_selected = df_all[(df_all["Scenario"] == EU_policy)
                         & (df_all["Year"] == run_year)
                         & (df_all["Climate Year"] == climate_year)
                        ]

    # drop the columns that consist of only NaNs
    df_selected = df_selected.dropna(axis=1, how="all")

    # create a list of all lines
    line_list_all = df_selected["Node/Line"].unique().tolist()

    # loop over sheets to read in the data
    export_all_df = pd.DataFrame()
    export_selected_df = pd.DataFrame()
    import_all_df = pd.DataFrame()
    import_selected_df = pd.DataFrame()

    # lists to store not fully defined lines
    lines_missing_export = []
    lines_missing_import = []
    lines_multiple_export = []
    lines_multiple_import = []

    for line in line_list_all:
        # find the values with line as Node/Line, and Parameter as Export Capacity (MW)
        export_temp_df = df_selected[(df_selected["Node/Line"] == line) & (df_selected["Parameter"] == "Export Capacity (MW)")]
        if export_temp_df.shape[0] == 1:
            export_all_df.loc[line, "Export Capacity (MW)"] = export_temp_df["Value"].values[0]

            # if line does not include any of the elements in elements_excluded, add it to the export_selected_df
            if not any(ele in line for ele in elements_excluded):
                export_selected_df.loc[line, "Export Capacity (MW)"] = export_temp_df["Value"].values[0]
        elif export_temp_df.shape[0] == 0:
            lines_missing_export.append(line)
        elif export_temp_df.shape[0] > 1:
            lines_multiple_export.append(line)

        # find the values with line as Node/Line, and Parameter as Import Capacity (MW)
        import_temp_df = df_selected[(df_selected["Node/Line"] == line) & (df_selected["Parameter"] == "Import Capacity (MW)")]
        if import_temp_df.shape[0] == 1:
            import_all_df.loc[line, "Import Capacity (MW)"] = - import_temp_df["Value"].values[0]
            
            # if line does not include any of the elements in elements_excluded, add it to the import_selected_df
            if not any(ele in line for ele in elements_excluded):
                import_selected_df.loc[line, "Import Capacity (MW)"] = import_temp_df["Value"].values[0]

        elif import_temp_df.shape[0] == 0:
            lines_missing_import.append(line)
        elif import_temp_df.shape[0] > 1:
            lines_multiple_import.append(line)
    
    export_import_selected_df = pd.merge(export_selected_df, import_selected_df, how='outer', left_index=True, right_index=True)
    
    # print items in lines_missing_import if the item does not contain  any of the items in elements_excluded 
    # (these are lines that are not in the model)
    lines_missing_import = [item for item in lines_missing_import if not any(ele in item for ele in elements_excluded)]
    lines_missing_export = [item for item in lines_missing_export if not any(ele in item for ele in elements_excluded)]
    lines_multiple_import = [item for item in lines_multiple_import if not any(ele in item for ele in elements_excluded)]
    lines_multiple_export = [item for item in lines_multiple_export if not any(ele in item for ele in elements_excluded)]

    if len(lines_missing_import) > 0:
        logging.warning(f"Lines missing import capacity: {lines_missing_import}")
    if len(lines_missing_export) > 0:
        logging.warning(f"Lines missing export capacity: {lines_missing_export}")
    if len(lines_multiple_import) > 0:
        logging.warning(f"Lines with multiple import capacities: {lines_multiple_import}")
    if len(lines_multiple_export) > 0:
        logging.warning(f"Lines with multiple export capacities: {lines_multiple_export}")

    return export_all_df, import_all_df, export_selected_df, import_selected_df, export_import_selected_df

# read in the data and write to csvs ----------------------------------------------------------
for run_year in PECD_data_years_list:
    for EU_policy, EU_policy_long in EU_policy_spaced_dict.items():
        for climate_year in climate_years_list:
            print("Reading NTC data for ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy, 90*"-")
            export_all_df, import_all_df, export_selected_df, import_selected_df, export_import_selected_df= read_data_NTC(EU_policy_long, run_year, climate_year)
            # write the data to csv file
            EU_policy_no_spaces = EU_policy_dict[EU_policy]
            export_all_df.to_csv(target_output_dir + "NTC_export_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            import_all_df.to_csv(target_output_dir + "NTC_import_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            export_selected_df.to_csv(target_output_dir + "NTC_export_selected_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            import_selected_df.to_csv(target_output_dir + "NTC_import_selected_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            export_import_selected_df.to_csv(target_output_dir + "NTC_export_import_selected_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            

# sanity checks -----------------------------------------------
# read all export_import_selected_df files and write to one file
# find all files in the target_output_dir that start with "NTC_export_import_selected_"
os.chdir(target_output_dir)
extension = 'csv'
all_filenames = [i for i in glob.glob('NTC_export_import_selected_*.{}'.format(extension))]

# loop over all files, read them in and write to one file
export_import_selected_all_df = pd.DataFrame()
for file in all_filenames:
    scen_name = file.split("_")[4]
    run_year = file.split("_")[5]

    # read in the file
    df = pd.read_csv(file, index_col=0)
    
    # add scenario and run_year to the column names
    df = df.add_prefix(scen_name + "_" + run_year + "_")

    export_import_selected_all_df = pd.concat([export_import_selected_all_df, df], axis=1)

export_import_selected_all_df.to_csv("all_NTC_export_import_selected.csv", index=True)
