import pandas as pd
import logging	# for logging
import os	    # for changing the working directory
import glob


# define paths ---------------------------------------------------------------
climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022//"
target_output_dir = r"inputs_to_model//NTC//"

# define years ---------------------------------------------------------------
# years for which capacity factor is available
PECD_data_years_list = [2050,] # 2030, 2025, 2040

# target climate years
climate_years_list = [2008, 2009, 1995]

# Options ---------------------------------------------------------------------
merge_some_countries = True # if True, the data for several regions in Italy (and also Luxembourg) are merged into IT00 (and LU00)
target_merge_countries = [
    # "IT", # unnecessary to include IT, as NTC data only has IT00 already
    "LU",
    "PL",
    ] # countries to merge


# policy scenario
EU_policy_dict = {
    "DE": "DistributedEnergy" ,
    "GA": "GlobalAmbition",
    }

EU_policy_spaced_dict = {
    "DE": "Distributed Energy" ,
    "GA": "Global Ambition",
    }

# create target_output_dir if does not exist
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)
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


            # merging multiple parallel lines -----------------------------------------------

def merge_parallel_lines(df):
    """	
    Merge parallel lines in the dataframe df.
    The parallel lines are lines that have the same name except for the last character (ending in ["Concept", "Virtual", "Real", "Expansion"]).
    The values in the parallel lines are summed and the index is renamed to the name of the first line.
    The dataframe with the merged lines is returned.
    """
    element_groups_in_para = ["Concept", "Virtual", "Real"]
    elements_items = [" " + element_groups_in_para[i] + " " + str(j) for i in range(len(element_groups_in_para)) for j in range(1, 6)]

    # reset index
    df = df.reset_index()

    # rename all cells that contain any of the elements in element_groups_in_para by removing the element from the cell
    for element in elements_items:
        df["index"] = df["index"].str.replace(element, "")

    # group by the index and sum the values in the same group
    df_new = df.groupby("index").sum()

    # set the column index as the index of the dataframe
    df_new = df_new.set_index(df_new.index)
    return df_new

def merge_country_regions_lines(imp_exp_df):
    """
    Merge the regions in the list target_merge_countries into one region.
    The regions are merged into the region with the name of the country + "00".
    The values in the merged regions are summed and the index is renamed to the name of the first region.
    The dataframe with the merged regions is returned.
    """

    # all_countries_in_df is the list of nodes in the index of imp_exp_df. The nodes are defined as the parts of the index before and after the first "-".
    all_first_nodes_in_df = [node.split("-")[0] for node in imp_exp_df.index]
    all_second_nodes_in_df = [node.split("-")[1] for node in imp_exp_df.index]
    all_nodes_in_df = list(set(all_first_nodes_in_df + all_second_nodes_in_df))


    for country in target_merge_countries:
        regions_in_target_country = [region for region in all_nodes_in_df if region.startswith(country)]


        # remove duplicates from regions_in_target_country
        regions_in_target_country = list(set(regions_in_target_country)- set([country + "00"])) 
        

        if len(regions_in_target_country) > 0:
            # if an index contains any of the values in regions_in_target_country, replace that part of the index with country + "00"
            for region in regions_in_target_country:
                imp_exp_df.index = imp_exp_df.index.str.replace(region, country + "00")
            
            # sum of the rows with the same index
            imp_exp_df = imp_exp_df.groupby(imp_exp_df.index).sum()


        # loop over every row, if an index contains str.split("-")[0] == str.split("-")[1] (e.g. PL00-PL00), remove the row
        for index in imp_exp_df.index:
            if index.split("-")[0] == index.split("-")[1]:
                try:
                    imp_exp_df = imp_exp_df.drop(index=index)
                except:
                    print(f"index {index} not in index of imp_exp_df")
            

        # imp_exp_df.loc["PL00-DE00"]
    return imp_exp_df


def remove_duplicate_reverse_lines(exp_df, imp_df):
    """
    For reverse lines, create one entry per export and import (to avoid having PL00-DE00 and DE00-PL00 lines at the same time).
    """
    def find_duplicate_index(df):
        line_name_list = df.index

        # find lines whose reverse is also in the index -----------------------------------------------
        # list of the reverse lines (if a line has its own reverse also in the index, it will be stored here)
        duplicate_lines_list = []
        # loop over index of imp_exp_df
        for line_name in line_name_list:

            # find the first and second node in the index
            first_node = line_name.split("-")[0]
            second_node = line_name.split("-")[1]
            reverse_line = second_node + "-" + first_node

            if reverse_line in line_name_list:
                if line_name not in duplicate_lines_list:
                    duplicate_lines_list = duplicate_lines_list + [reverse_line]
    
        return duplicate_lines_list

    duplicate_lines_exp = find_duplicate_index(exp_df)
    duplicate_lines_imp = find_duplicate_index(imp_df)

    # merge the two lists and keep unique values
    duplicate_lines_list = list(set(duplicate_lines_exp + duplicate_lines_imp))

    # remove duplicate lines and their reverse from exp_df and imp_df -----------------------------------------------
    exp_original_df = exp_df.copy()
    imp_original_df = imp_df.copy()

    # remove rows that have line or reverse_line as index, if the row exists ---------------------------------------
    for line in duplicate_lines_list:
        reverse_line = line.split("-")[1] + "-" + line.split("-")[0]

        try:
            exp_df = exp_df.drop(index=line)
        except KeyError:
            pass
        
        try:
            exp_df = exp_df.drop(index=reverse_line)
        except KeyError:
            pass

        try:
            imp_df = imp_df.drop(index=line)
        except KeyError:
            pass

        try:
            imp_df = imp_df.drop(index=reverse_line)
        except KeyError:
            pass


    # add back the values of duplicate_lines_list to exp_df and imp_df -----------------------------------------------
    for line in duplicate_lines_list:
        first_node = line.split("-")[0]
        second_node = line.split("-")[1]
        reverse_line = second_node + "-" + first_node

        # below are equations used to merge values (if reverse exists or not)
        try:
            exp_org_value = exp_original_df.loc[line].values[0]
        except KeyError:
            exp_org_value = 0

        try:
            exp_reverse_value = imp_original_df.loc[reverse_line].values[0]
        except KeyError:
            exp_reverse_value = 0

        try:
            imp_org_value = imp_original_df.loc[line].values[0]
        except KeyError:
            imp_org_value = 0

        try:
            imp_reverse_value = exp_original_df.loc[reverse_line].values[0]
        except KeyError:
            imp_reverse_value = 0

        exp_df.loc[line] = exp_org_value + exp_reverse_value
        imp_df.loc[line] = imp_org_value + imp_reverse_value

    return exp_df, imp_df

# read in the data and write to csvs ----------------------------------------------------------
for run_year in PECD_data_years_list:
    for EU_policy, EU_policy_long in EU_policy_spaced_dict.items():
        for climate_year in climate_years_list:
            print("Reading NTC data for ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy, 90*"-")
            export_all_df, import_all_df, *rest_of_dataframes= read_data_NTC(EU_policy_long, run_year, climate_year)
            # merging multiple lines of the same country, removing H2 lines etc.
            # export_all_df.loc["PLE0-DE00"]

            # removing H2 related lines -----------------------------------------------
            elements_excluded_H2 = ["EV2","EV2W", "EV2W V2G", "H2MT", "SNR1", "H2R1", "RETE", "HER4", ]

            # remove all rows if the index contains any of the elements in elements_excluded_H2
            export_df = export_all_df[~export_all_df.index.str.contains('|'.join(elements_excluded_H2))]
            import_df = import_all_df[~import_all_df.index.str.contains('|'.join(elements_excluded_H2))]

            export_df = merge_parallel_lines(export_df)
            import_df = merge_parallel_lines(import_df)

            # merge regions in target_merge_countries into one region
            if merge_some_countries:
                export_df = merge_country_regions_lines(export_df)
                import_df = merge_country_regions_lines(import_df)



            # remove duplicate reverse lines (and add them to the first line) - e.g. PL00-DE00 and DE00-PL00
            export_df, import_df = remove_duplicate_reverse_lines(export_df, import_df)
            
            # write the data to csv file
            EU_policy_no_spaces = EU_policy_dict[EU_policy]
            export_df.to_csv(target_output_dir + "NTC_export_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)
            import_df.to_csv(target_output_dir + "NTC_import_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)




# sanity checks -----------------------------------------------
# read all export_import_selected_df files and write to one file
# find all files in the target_output_dir that start with "NTC_export_import_selected_"
os.chdir(target_output_dir)
extension = 'csv'
all_filenames = [i for i in glob.glob('NTC_*.{}'.format(extension))]

# loop over all files, read them in and write to one file
export_import_selected_all_df = pd.DataFrame()
for file in all_filenames:
    scen_name = file.split("_")[2]
    run_year = file.split("_")[3]

    # read in the file
    df = pd.read_csv(file, index_col=0)
    
    # add scenario and run_year to the column names
    df = df.add_prefix(scen_name + "_" + run_year + "_")

    export_import_selected_all_df = pd.concat([export_import_selected_all_df, df], axis=1)

export_import_selected_all_df.to_csv("all_NTC_export_import_selected2.csv", index=True)
