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
# climate_year = 1995
# run_year = 2050

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

def negate_flows(df, target_country, lines_outside_country_list):
    """	
    This function calculates the exprots for target_country.
    Values in clumn Value will considered as positve export if 
        1. target_country is the first part of the node name and the column Parameter has the value "Flow (GWh)"
        2. target_country is the second part of the node name and the column Parameter has the value "Flow Back (GWh)"
    Values in clumn Value will considered as negative export if 
        1. target_country is the first part of the node name and the column Parameter has the value "Flow Back (GWh)"
        2. target_country is the second part of the node name and the column Parameter has the value "Flow (GWh)"
    """
    df = df[df["Node/Line"].isin(lines_outside_country_list)]
    df = df[df["Parameter"].str.contains("Flow")]
    # df = df[["Node/Line", "Parameter", "Value"]]

    for idx, row in df.iterrows():
        node_parts = row['Node/Line'].split('-')
        # in every row of df, if target_country in row["Node/Line"].split("-")[1] and target_parameter == "Flow (GWh)", negate the value in column Value
        if target_country in node_parts[1] and row['Parameter'] == "Flow (GWh)":
            df.at[idx, 'Value'] = -row['Value']

        # if target_country in row["Node/Line"].split("-")[0] and target_parameter == "low Back (GWh)", negate the value in column Value
        elif target_country in node_parts[0] and row['Parameter'] == "Flow Back (GWh)":
            df.at[idx, 'Value'] = -row['Value']

    return df


def export_cal_country(df, target_country, target_scenario, target_year, target_climate_year):
    # keep the part of df that have column "Scenario" equal to target_scenario	and column "Year" equal to target_year
    df = df[(df["Scenario"] == target_scenario) & (df["Year"] == target_year)]

    # keep the part of df that have column "Climate Year" equal to target_climate_year
    df = df[df["Climate Year"] == target_climate_year]

    # find all nodes that have target_country as part of their "Node/Line"  column
    line_list = df[df["Node/Line"].str.contains(target_country)]["Node/Line"].unique()

    # # lines_country_list is all the lines whose "Node/Line" column is in mp.Map_countryname_nodes[target_country]
    # lines_country_list = [line for line in df["Node/Line"].to_list() if line in mp.Map_countryname_nodes[target_country]]
    



    # keep part of df that have column "Node/Line" in nodes_list
    df = df[df["Node/Line"].isin(line_list)]

    # internal flows: within the node_list, find the nodes that have DE twice
    lines_within_country_list = [node for node in line_list if node.count(target_country) == 2]

    # external flows: nodes that have target country only once
    lines_outside_country_list = [node for node in line_list if node.count(target_country) == 1]

    # correct the sign of the flows for lines_outside_country_list
    exports_from_target_country = negate_flows(df,target_country, lines_outside_country_list)

    # exports via H2 connections
    lines_H2 = [line for line in lines_outside_country_list if line.count("H2") >= 1]

    H2_exports_from_target_country = negate_flows(df, target_country, lines_H2)

    # exchanges of H2 within the country
    lines_H2_within_country = [line for line in lines_within_country_list if line.count("H2") == 2]
    H2_exports_within_country = negate_flows(df, target_country, lines_H2_within_country)

    # exhanges within a country between a H2 node and a electricity node
    lines_H2_electricity = [line for line in lines_within_country_list if line.count("H2") == 1]
    electricity_H2_exports_within_country = negate_flows(df, target_country, lines_H2_electricity)

    # exchanges within a country without H2 nodes
    lines_electricity = [line for line in lines_within_country_list if line.count("H2") == 0]
    exports_within_country_electricity = negate_flows(df, target_country, lines_electricity)

    # create a list of all elements in lines_electricity defined as line.split("-")[0] line.split("-")[1]
    nodes_electricity_list = [line.split("-")[0] for line in lines_electricity] + [line.split("-")[1] for line in lines_electricity]

    # find unique elements in lines_electricity_list and create a list of them
    nodes_electricity_list = list(set(nodes_electricity_list))

    # remove target_country from lines_electricity_list
    if target_country + "00" in nodes_electricity_list:
        nodes_electricity_list.remove(target_country+ "00")

    # find lines lines_electricity that include nodes_electricity_list
    unique_node_to_lines = {}
    for node in nodes_electricity_list:
        unique_node_to_lines[node] = [line for line in lines_electricity if node in line]

    nodes_electric_data = {}
    for node, lines in unique_node_to_lines.items():
        nodes_electric_data[node] = negate_flows(df, target_country, lines)




    return (
        exports_from_target_country, 
        exports_from_target_country.Value.sum(), 
        H2_exports_from_target_country, 
        H2_exports_from_target_country.Value.sum(),
        H2_exports_within_country,
        H2_exports_within_country.Value.sum(),
        electricity_H2_exports_within_country,
        electricity_H2_exports_within_country.Value.sum(),
        exports_within_country_electricity,
        exports_within_country_electricity.Value.sum(),
        nodes_electric_data
        )


# import the xlsx file C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\220310_Updated_Electricity_Modelling_Results.xlsx 
# into a dataframe called df
# flows_all_df = pd.read_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\220310_Updated_Electricity_Modelling_Results - Kopie.xlsx", sheet_name="Line")
flows_all_df = pd.read_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\220310_Updated_Electricity_Modelling_Results.xlsx", sheet_name="Line")


# remove columns that have only NaN values
flows_all_df = flows_all_df.dropna(axis=1, how="all")

# create a list of all lines
line_list_all = flows_all_df["Node/Line"].unique()

# H2 to H2 trade: find the list of lines that have "H2" twice in its name
line_H2_H2 = [line for line in line_list_all if line.count("H2") == 2]

# H2 to X trade: find the list of lines that have "H2" once in its name
line_H2_X = [line for line in line_list_all if line.count("H2") == 1]

# H2 to external (outside the country) X trade: list of trades between a main market and H2 node in another country
line_H2_X_external = [line for line in line_H2_X  if line.split("-")[0][0:4] != line.split("-")[1][0:4]]

if line_H2_X_external == []:
    print("There is no H2 node connected to a electricity node outside the country")


for scen_short, scen_long in EU_policy_spaced_dict.items():
    for run_year in run_year_list:
        print(f"reading scenario : {scen_long}  - run_year: {run_year}")
        for climate_year in climate_years_list:
            exports_all = pd.DataFrame()
            exports_all_sum = pd.DataFrame(columns=["sum"])
            exports_H2 = pd.DataFrame()
            exports_H2_sum = pd.DataFrame(columns=["sum"])
            exports_within_country_H2 = pd.DataFrame()
            exports_within_country_H2_sum = pd.DataFrame(columns=["sum"])
            exports_within_country_electricity_H2 = pd.DataFrame()
            exports_within_country_electricity_H2_sum = pd.DataFrame(columns=["sum"])
            exports_within_country_electricity = pd.DataFrame()
            exports_within_country_electricity_sum = pd.DataFrame(columns=["sum"])
            nodes_electric_data = {}



            # order mp.Map_countryname_nodes.keys() alphabetically
            sorted_keys = sorted(mp.Map_countryname_nodes.keys())

            # find values in mp.Map_countryname_nodes.keys() that are floats
            float_keys = [key for key in mp.Map_countryname_nodes.keys() if isinstance(key, float)]


            for target_country in target_country_list:
                (
                    exports_from_target_country, 
                    exports_from_target_country_sum,
                    H2_exports_from_target_country,
                    H2_exports_from_target_country_sum,
                    H2_exports_within_country,
                    H2_exports_within_country_sum,
                    electricity_H2_exports_within_country,
                    electricity_H2_exports_within_country_sum,
                    exports_within_country_electricity_,
                    exports_within_country_electricity_sum_,
                    nodes_electric_data_
                ) = export_cal_country(flows_all_df, target_country, scen_long, run_year, climate_year)
                exports_all = pd.concat([exports_all, exports_from_target_country])
                exports_all_sum.loc[target_country,"sum"] = exports_from_target_country_sum
                exports_H2 = pd.concat([exports_H2, H2_exports_from_target_country])
                exports_H2_sum.loc[target_country,"sum"] = H2_exports_from_target_country_sum
                exports_within_country_H2 = pd.concat([exports_within_country_H2, H2_exports_within_country])
                exports_within_country_H2_sum.loc[target_country,"sum"] = H2_exports_within_country_sum
                exports_within_country_electricity_H2 = pd.concat([exports_within_country_electricity_H2, electricity_H2_exports_within_country])
                exports_within_country_electricity_H2_sum.loc[target_country,"sum"] = electricity_H2_exports_within_country_sum
                exports_within_country_electricity = pd.concat([exports_within_country_electricity, exports_within_country_electricity_])
                exports_within_country_electricity_sum.loc[target_country,"sum"] = exports_within_country_electricity_sum_
                nodes_electric_data[target_country] = nodes_electric_data_

            # if target_output_dir does not exist, create it
            if not os.path.exists(target_output_dir):
                os.makedirs(target_output_dir)

            scen_long_no_space = scen_long.replace(" ", "")
            exports_all_sum.to_csv(f"{target_output_dir}//exportsAllSum_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_all.to_csv(f"{target_output_dir}//exportsAll_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_H2_sum.to_csv(f"{target_output_dir}//exportsH2Sum_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_H2.to_csv(f"{target_output_dir}//exportsH2_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_H2_sum.to_csv(f"{target_output_dir}//exportsWithinCountryH2Sum_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_H2.to_csv(f"{target_output_dir}//exportsWithinCountryH2_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_electricity_H2_sum.to_csv(f"{target_output_dir}//exportsWithinCountryElectricityH2sum_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_electricity_H2.to_csv(f"{target_output_dir}//exportsWithinCountryElectricityH2_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_electricity_sum.to_csv(f"{target_output_dir}//exportsWithinCountryElectricitySum_{scen_long_no_space}_{run_year}_{climate_year}.csv")
            exports_within_country_electricity.to_csv(f"{target_output_dir}//exportsWithinCountryElectricity_{scen_long_no_space}_{run_year}_{climate_year}.csv")


# # for every country in keys of nodes_electric_data, merge all the dataframes in nodes_electric_data[country] into one dataframe, and save to an excel file with sheet name = country
# for country, data in nodes_electric_data.items():
#     if data != {}:
#         nodes_electric_data[country] = pd.concat(data.values(), axis=0, keys=data.keys())
#         nodes_electric_data[country].to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\nodes_electric_data_" + country + ".xlsx")