import pandas as pd
# This file includes all functions that are take some initial input files (e.g., csv files) and create intermediate files that are directly imported in the model runs.
# This approach (creating files that are directly imported in the model runs) is used to avoid the need to re-run some of teh data preparation code every time the model is run.
# The data preparation code is run only when the initial files are changed.


# # write a function to read input/availability_factor_conventional.csv


# df = pd.read_csv(r'input/availability_factor_conventional.csv', header=0, index_col=0)

# def read_availability_factor_conventional():
#     # read input/availability_factor_conventional.csv
#     df = pd.read_csv(r'input/availability_factor_conventional.csv', header=0, index_col=0)
#     # add a column to df with name t and values between t_1 and t_8760
#     df.insert(0, 't', ['t_' + str(i) for i in range(1, 1 + len(df))])
#     # save the dataframe df to csv file named availability_factor_conventional.csv
#     df.to_csv(r'input/availability_factor_conventional.csv', index=False)
#     return df
year = 2025


def serialize_key(key):
    if isinstance(key, tuple):
        return str(key)
    return key


year = 2030


def read_transfer_capacities(year):  # year is 2025 or 2030
    """
    Read net transfer capacities data from xlsx file and store data in json files.
    Vriables:
        Line_list: list of lines, e.g. Line_list ['HVAC_AT00_CH00'...
        Map_line_node: start and end node of each line. e.g. {'HVAC_AT00_CH00': {'start_node': 'AT00', 'end_node': 'CH00'},...
        ATC_exportlimit: export limit of each line. e.g. ('HVAC_AT00_SI00', 't_3563'): 550
        ATC_importlimit: import limit of each line. e.g. ('HVAC_FR00_CH00', 't_505'): 1400
    Output: 
        json files named List_line_year.json, Map_line_node_year.json, ATC_exportlimit_year.json, ATC_importlimit_year.json
    """
    from mappings import region_list
    import json
    Line_list = []
    Map_line_node = {}
    ATC_exportlimit = {}
    ATC_importlimit = {}
    for sheet in ['HVAC', 'HVDC']:
        xls = pd.read_excel(r'input/NTC/Transfer_Capacities_ERAA2021_TY' +
                            str(year) + '.xlsx', sheet_name=sheet, header=9)
        
        # quick fixes --------------------------------------------------------------------------------------------
        # replace any cells of DKkf with DKKF, as it is a mistake in the dataset
        xls = xls.replace(to_replace="DKkf", value="DKKF")

        # replace any cells of ITCA with ITS1, as the generation capacity dataset has the two regions of ITS1 and ITCA merged
        xls = xls.replace(to_replace="ITCA", value="ITS1")

        # replace nodes that are in the network file but not in region list --------------------------------------
        # (e.g., a node called in NTC as PLE0 should be renamed to PL00)

        # create intermediate lists and dictionary to help replcae  ---------------------
        # list of country codes in the region_list
        country_codes_in_region_list = [x[:2] for x in region_list]
        
        # remove duplicatews from country_codes_in_region_list
        country_codes_in_region_list = list(dict.fromkeys(country_codes_in_region_list))

        # list of all regions in the source file
        all_regions_in_file = xls.iloc[0, :].tolist() + xls.iloc[1, :].tolist()

        # remove duplicates from all_regions_in_file
        all_regions_in_file = list(dict.fromkeys(all_regions_in_file))

        # remove nan , "To:" and "From:" from all_regions_in_file
        all_regions_in_file = [x for x in all_regions_in_file if str(x) != 'nan' and str(x) != "To:" and str(x) != "From:"]

        # if a region in all_regions_in_file is not in region_list, but its country code is in country_codes_in_region_list, then save it in a dictionary
        # this dictionary is used to map the region names in the file to the region names in region_list
        # e.g., Map_region_name["PLE0"] = "PL00"
        Map_region_name = {}
        for region in all_regions_in_file:
            if region not in region_list and region[:2] in country_codes_in_region_list:
                Map_region_name[region] = region[:2] + "00"

        # replacing values in xls -----------------------------------------------------------
        # wherever in xls there is a cells of any of the keys (e.g., "PLE0") in Map_region_name, replace it with the corresponding value Map_region_name (PL00)
        xls = xls.replace(to_replace=Map_region_name)

        # further adjustments needed (1.remove lines within a node, 2. merge duplicates)------

        # 1. remove lines that are now within the same region
        # if row 1 and 2 of a column has identical values, then remove the column, as this column is just including the newly created lines within a region
        for column_name in xls.columns:
            if xls[column_name][0] == xls[column_name][1]:
                print("removing column ", xls[column_name][0] + '-' + xls[column_name][1])
                xls = xls.drop(columns=[column_name])

        # 1.5 rename columns to new correct names (e.g., PLE0-CZ00 to PL00-CZ00))                
        # rename all column names to the first row "-" second row
        xls.columns = xls.iloc[0, :] + '-' + xls.iloc[1, :]

        # 2. if two columns of xls have the same column name, then remvoe them and replace a new column with the first column name and 3 first elements and sum the rest of the rows

        # Find duplicated column names
        duplicated_columns = xls.columns[xls.columns.duplicated(keep='first')]

        # Iterate through duplicated columns
        for column_name in duplicated_columns:
            merged_df = pd.DataFrame()
            merged_df = xls[column_name].iloc[3:].sum(axis=1).to_frame()
            # rename the column in merged_df as column_name
            merged_df.columns = [column_name]
            print(merged_df)
            # add xls[column_name].iloc[3:,0] to to top of merged_df
            merged_df = pd.concat([xls[column_name].iloc[:3, 0].to_frame(), merged_df])
            print(merged_df)

            # remove all columns with name column_name from xls
            xls = xls.drop(columns=[column_name])

            # add merged_df to xls
            xls = pd.concat([xls, merged_df], axis=1)
        
       
        # a list to store only the lines in the sheet, so that we can loop properly only within the sheet
        Line_list_sheet = []

        # create output files for the model --------------------------------------------------------------------------------------------
        # create a list of all lines in xls and save it in Line_list (and update Map_line_node)
        for column_name in xls.columns[2:]:
            # separate column_name at the string " - "
            start, end = column_name.split("-")
            if start in region_list and end in region_list:
                line_name = sheet + '_' + start + '_' + end
                reversed_line_name = sheet + '_' + end + '_' + start

                # if the line (its reverse version) is not already in the list, then add it to the list and update Map_line_node
                if reversed_line_name not in Line_list:
                    Line_list.append(line_name)
                    Line_list_sheet.append(line_name)
                    Map_line_node[line_name] = {}
                    Map_line_node[line_name]["start_node"] = start
                    Map_line_node[line_name]["end_node"] = end

        for line_name in Line_list_sheet:
            # column name is equal to start + '-' + end
            column_name = Map_line_node[line_name]["start_node"] + \
                '-' + Map_line_node[line_name]["end_node"]
            
            for t in range(len(xls[column_name])-3):
                ATC_exportlimit[line_name, "t_" +
                                str(t+1)] = xls[column_name][t+3]
            
            # import values in the column to ATC_importlimit, if exists
            column_name_reverse = Map_line_node[line_name]["end_node"] + \
                '-' + Map_line_node[line_name]["start_node"]
            
            if column_name_reverse in xls.columns:
                for t in range(len(xls[column_name_reverse])-3):
                    try:
                        ATC_importlimit[line_name, "t_" + \
                                        str(t+1)] = xls[column_name_reverse][t+3]
                    except KeyError:  # the return value of column is not available in the file, so I assume 0
                        ATC_importlimit[line_name, "t_" + str(t+1)] = 0
            else:
                print("column_name_reverse ", column_name_reverse, " not in xls.columns")
                for t in range(len(xls[column_name])-3):
                    ATC_importlimit[line_name, "t_" +
                                    str(t+1)] = 0

    # save List_line, Map_line_node, ATC_exportlimit, ATC_importlimit to json files named List_line_year.json, Map_line_node_year.json, ATC_exportlimit_year.csv, ATC_importlimit_year.csv
    with open(r'input/NTC/List_line_' + str(year) + '.json', 'w') as fp:
        json.dump(Line_list, fp, indent=4)

    with open(r'input/NTC/Map_line_node_' + str(year) + '.json', 'w') as fp:
        json.dump(Map_line_node, fp, indent=4)

    # write ATC_exportlimit_year.csv
    df = pd.DataFrame.from_dict(ATC_exportlimit, orient='index')
    df.index = pd.MultiIndex.from_tuples(df.index, names=['line_name', 't'])
    df = df.reset_index()
    df.columns = ['line_name', 't', 'value']
    df.to_csv(r'input/NTC/ATC_exportlimit_' + str(year) + '.csv', index=False)

    df = pd.DataFrame.from_dict(ATC_importlimit, orient='index')
    df.index = pd.MultiIndex.from_tuples(
        df.index, names=['line_name', 't'])
    df = df.reset_index()
    df.columns = ['line_name', 't', 'value']
    df.to_csv(r'input/NTC/ATC_importlimit_' + str(year) + '.csv', index=False)
    return


for year in [2025, 2030]:
    read_transfer_capacities(year)


# import pandas as pd

# weather_years_list = [1982, 1984, 1985, 1997, 2007,2009]

# def PECD_wind_PV_data_reformat_to_csv(weather_years_list):
#     """"
#     This file is used to reformat the PECD_LFSolarPV_2030_edition 2021.3.xlsx file to csv files for each weather year.
#     Ideally, this should be used only once. The csv files are saved in \input\RES_PECD.
#     """
#     for RES_tech in ['Offshore', 'Onshore', 'LFSolarPV']:
#         xls = pd.ExcelFile(r'C:/Models/Future_Markets/input/RES_PECD/PECD_' + RES_tech + '_2030_edition 2021.3.xlsx')
#         sheets = xls.sheet_names
#         print('sheets are ', sheets)
#         print(RES_tech + 100*'=')
#         for weahter_year in weather_years_list:
#             print(weahter_year)
#             print(60*'-')
#             df = pd.DataFrame()
#             for region in sheets:
#                 print(region)
#                 # read xlsx file PECD_LFSolarPV_2030_edition 2021.3.xlsx
#                 df_temp = pd.read_excel(r'C:/Models/Future_Markets/input/RES_PECD/PECD_' + RES_tech + '_2030_edition 2021.3.xlsx', sheet_name=region, header=10)
#                 # add df_temp[weahter_year]] to the dataframe df using concant as a column and name the column region
#                 df = pd.concat([df, df_temp[weahter_year].rename(region)], axis=1)  #, keys=[region]
#             # add a column to df with name t and values between t_1 and t_8760
#             df.insert(0, 't', ['t_' + str(i) for i in range(1, 1 + len(df))])
#             # save the dataframe df to csv file named PECE_solar_weather_year.csv
#             df.to_csv(r'C:/Models/Future_Markets/input/RES_PECD/PECD_' + RES_tech + '_' + str(weahter_year) +'.csv', index=False)
