import pandas as pd


# define paths ---------------------------------------------------------------
climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\TYNDP_2022//"
target_output_dir = r"RES_availability_factor_PECD//"

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


# functions      -----------------------------------------------------------
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


    # create a list of all lines
    line_list_all = df_selected["Node/Line"].unique().tolist()

    # loop over sheets to read in the data
    export_df = pd.DataFrame()
    import_df = pd.DataFrame()

    for line in line_list_all:
        # find the values with line as Node/Line, and Parameter as Export Capacity (MW)
        export_temp_df = df_selected[(df_selected["Node/Line"] == line) & (df_selected["Parameter"] == "Export Capacity (MW)")]
        export_df.loc[line, "Export Capacity (MW)"] = export_temp_df["Value"].values[0]

        # find the values with line as Node/Line, and Parameter as Import Capacity (MW)
        import_temp_df = df_selected[(df_selected["Node/Line"] == line) & (df_selected["Parameter"] == "Import Capacity (MW)")]
        import_df.loc[line, "Import Capacity (MW)"] = import_temp_df["Value"].values[0]



    return df

# read in the data and write to csvs ----------------------------------------------------------
for run_year in PECD_data_years_list:
    for EU_policy, EU_policy_long in EU_policy_spaced_dict.items():
        for climate_year in climate_years_list:
            print("Reading NTC data for ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy)
            availability_factor_df = read_data_NTC(EU_policy_long, run_year, climate_year)
            # write the data to csv file
            availability_factor_df.to_csv(target_output_dir + "NTC _" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)

