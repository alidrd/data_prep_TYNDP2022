import pandas as pd
import os
import glob


# define paths ---------------------------------------------------------------
climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\Climate Data"
target_output_dir = r"inputs_to_model/RES_availability_factor_PECD//"

# define options -------------------------------------------------------------
merge_some_countries = True # if True, the data for several regions in Italy (and also Luxembourg) are merged into IT00 (and LU00)
target_merge_countries = ["IT",] # countries to merge

# weights for the merge, installed capacities copied from  TYNDP 2020, 2040, Global Ambitions, file TYNDP-2020-Scenario-Datafile.xlsx
weights = {"IT":
           {"windon":
                    {"ITCN" : 318,
                     "ITCS" : 5111, 
                     "ITN1" : 375, 
                     "ITS1" : 11846, 
                     "ITSA" : 2322, 
                     "ITSI" : 3836, 
                     },
            "windof":
                    {"ITCN" : 0,
                     "ITCS" : 0, 
                     "ITN1" : 0, 
                     "ITS1" : 644, 
                     "ITSA" : 0, 
                     "ITSI" : 0, 
                    },
            "pv":
                    {"ITCN" : 4852, 
                     "ITCS" : 4890, 
                     "ITN1" : 33452, 
                     "ITS1" : 6411, 
                     "ITSA" : 1594, 
                     "ITSI" : 3192, 
                    },
           },
} 	

# define years ---------------------------------------------------------------
# years for which capacity factor is available
PECD_data_years_list = [2030, 2025]

# target climate years
climate_years_list = [2008, 2007, 1995]

# define mappings ------------------------------------------------------------
# technology mapping
technology_dict = {"pv": "LFSolarPV",
                   "windon" : "Onshore",
                   "windof" : "Offshore",
                   }

# Mappings of zones in the model 
Mapping_zone_country = {}
# read values in market_nodes.csv into a dictionary, where the key is data_granularity and the value is the country, using pandas
df = pd.read_csv("market_nodes.csv")
for index, row in df.iterrows():
    Mapping_zone_country[row["data_granularity"]] = row["country"]

# if target_output_dir does not exist, create it
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)

# functions      -----------------------------------------------------------
def read_data_RES(technology, PECD_year, climate_year):
    """
    Read in the data from the PECD file for the given technology, PECD year and climate year.
    The data is read from the sheet with the name of the country in the model.
    The data is read from the column with the name of the climate year.
    The data is renamed to the name of the country in the model.
    The index is renamed to "t_" + the row number.
    The data is returned as a dataframe.
    """
    # target xlsx file
    file_name = climate_data_dir + r"\PECD_" + technology_dict[technology] + "_" + PECD_year + "_edition 2021.3.xlsx"

    # get the name of all sheets in the file
    sheets = pd.ExcelFile(file_name).sheet_names

    # find sheet that are in the Mapping_zone_country but not in sheets
    missing_sheets = [sheet for sheet in Mapping_zone_country.keys() if sheet not in sheets]

    print("Regions in the model without availability factor in PECD: ", missing_sheets)

    # consider only sheets that are included in the keys of Mapping_zone_country
    sheets = [sheet for sheet in sheets if sheet in Mapping_zone_country.keys()]

    # loop over sheets to read in the data
    df = pd.DataFrame()
    for sheet in sheets:
        df_temp = pd.read_excel(file_name, sheet_name=sheet, header=10, index_col=False)

        # keep the columns with the climate year
        df_temp = df_temp.loc[:, climate_year]

        # rename the column to the sheet name
        df_temp = df_temp.rename(sheet)

        # rename the index to "t_" + the row number
        df_temp.index = ["t_" + str(i+1) for i in df_temp.index]

        # add the new column to the dataframe
        df = pd.concat([df, df_temp], axis=1)

    return df

def merge_availabilities(avail_df, tech):
    for country in target_merge_countries:
        avail_country_df = pd.DataFrame()

        # find the columns that start with country
        columns = [col for col in avail_df.columns if col.startswith(country)]

        # save columns in a new dataframe
        avail_country_df = avail_df[columns]

        # drop the columns
        avail_df = avail_df.drop(columns=columns)

        # add a new column named country + "00" to avail_df that comprises of avail_country_df weighted based on weights[country][tech] 
        avail_df[country + "00"] = (avail_country_df * weights[country][tech]).sum(axis=1) / sum(weights[country][tech].values())

    return avail_df
# read in the data and write to csvs ----------------------------------------------------------
for tech in technology_dict.keys():
    for climate_year in climate_years_list:
        for PECD_year in PECD_data_years_list:
            print("Reading RES data for ", tech, " for PECD year ", PECD_year, " and climate year ", climate_year)
            availability_factor_df = read_data_RES(tech, str(PECD_year), climate_year)

            if merge_some_countries:
                availability_factor_df = merge_availabilities(availability_factor_df, tech)
            # write the data to csv file
            availability_factor_df.to_csv(target_output_dir + tech + "_" + str(PECD_year) + "_" + str(climate_year) + ".csv", index=True)


# sanity checks on average availability factor -----------------------------------------------
# read the files created above, calculate the average and write to a new file
all_averages = pd.DataFrame()
os.chdir(target_output_dir)
extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
# loop over all files
for file in all_filenames:
    # read in the file
    df = pd.read_csv(file, index_col=0)
    
    # calculate the average
    df_average = df.mean(axis=0)
    
    # rename the column to the file name except the extension
    df_average = df_average.rename(file[:-4])

    # add the new column to the dataframe
    all_averages = pd.concat([all_averages, df_average], axis=1)


    # write to a new 
all_averages.to_csv("stats//averages.csv", index=True)