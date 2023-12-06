import pandas as pd


# define paths ---------------------------------------------------------------
climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\demand"
target_output_dir = r"demand//"

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

# Mappings of zones in the model 
Mapping_zone_country = {}
# read values in market_nodes.csv into a dictionary, where the key is data_granularity and the value is the country, using pandas
df = pd.read_csv("market_nodes.csv")
for index, row in df.iterrows():
    Mapping_zone_country[row["data_granularity"]] = row["country"]



# functions      -----------------------------------------------------------
def read_data_demand(EU_policy, run_year, climate_year):
    """
    Read in the data from the PECD file for the given technology, PECD year and climate year.
    The data is read from the sheet with the name of the country in the model.
    The data is read from the column with the name of the climate year.
    The data is renamed to the name of the country in the model.
    The index is renamed to "t_" + the row number.
    The data is returned as a dataframe.
    """
    # target xlsx file
    file_name = climate_data_dir + r"\Demand_TimeSeries_" + str(run_year) + "_" + EU_policy + r"_release.xlsb"

    # get the name of all sheets in the file
    sheets = pd.ExcelFile(file_name).sheet_names

    # find sheet that are in the Mapping_zone_country but not in sheets
    missing_sheets = [sheet for sheet in Mapping_zone_country.keys() if sheet not in sheets]

    print("Regions in the model without availability factor in PECD: ", missing_sheets)

    # # consider only sheets that are included in the keys of Mapping_zone_country
    # sheets = [sheet for sheet in sheets if sheet in Mapping_zone_country.keys()]

    # loop over sheets to read in the data
    df = pd.DataFrame()
    for sheet in sheets:
        df_temp = pd.read_excel(file_name, sheet_name=sheet, header=6, index_col=False)

        # keep the columns with the climate year
        df_temp = df_temp.loc[:, climate_year]

        # rename the column to the sheet name
        df_temp = df_temp.rename(sheet)

        # rename the index to "t_" + the row number
        df_temp.index = ["t_" + str(i+1) for i in df_temp.index]

        # add the new column to the dataframe
        df = pd.concat([df, df_temp], axis=1)

    return df

# read in the data and write to csvs ----------------------------------------------------------
for run_year in PECD_data_years_list:
    for EU_policy, EU_policy_long in EU_policy_dict.items():
        for climate_year in climate_years_list:
            for PECD_year in PECD_data_years_list:
                print("Reading demand data for ", run_year , " for climate_year year ", climate_year, " and EU policy ", EU_policy)
                availability_factor_df = read_data_demand(EU_policy, run_year, climate_year)
                # write the data to csv file
                availability_factor_df.to_csv(target_output_dir + "demand_" + EU_policy_long + "_" + str(run_year) + "_" + str(climate_year) + ".csv", index=True)

