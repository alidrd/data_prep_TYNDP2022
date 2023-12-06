import pandas as pd
import mappings_tyndp as mp


# target_country_list = ["CH", "DE", "FR", "AT", "IT", "CZ", "NL", "DK", "NO", "SE", "FI", "EE", "LV", "LT", "BE", "LU", "UK", "IE", "ES", "PT", "PL", "SI", "HR", "HU", "SK", "RO", "BG", "GR", "CY", "MT"]
target_country_list = ["Austria",
                        "Belgium",
                        "Corsica",
                        "Croatia",
                        "Czech Republic",
                        "Denmark" ,
                        "Estonia",
                        "Finland",
                        "France",
                        "Germany",
                        "Greece",
                        "Hungary",
                        "Ireland",
                        "Italy",
                        "Latvia",
                        "Lithuania",
                        "Luxembourg",
                        "Luxemburg",
                        "Malta",
                        "Netherlands",
                        "Northern Ireland",
                        "Norway",
                        "Poland" ,
                        "Portugal",
                        "Slovakia",
                        "Slovenia",
                        "Spain",
                        "Sweden",
                        "Switzerland",
                        "United Kingdom",]
target_scenario = "Global Ambition"  #Distributed Energy  #Global Ambition
target_climate_year = 1995
target_year = 2050


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


def export_cal_country(df, target_country):
    # keep the part of df that have column "Scenario" equal to target_scenario	and column "Year" equal to target_year
    df = df[(df["Scenario"] == target_scenario) & (df["Year"] == target_year)]

    # keep the part of df that have column "Climate Year" equal to target_climate_year
    df = df[df["Climate Year"] == target_climate_year]

    # find all nodes that have target_country as part of their "Node/Line"  column
    line_list = df[df["Node/Line"].str.contains(target_country)]["Node/Line"].unique()

    # lines_country_list is all the lines whose "Node/Line" column is in mp.Map_countryname_nodes[target_country]
    lines_country_list = [line for line in df["Node/Line"].to_list() if line in mp.Map_countryname_nodes[target_country]]
    



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
flows_all_df = pd.read_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\220310_Updated_Electricity_Modelling_Results - Kopie.xlsx", sheet_name="Line")

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
    print(target_country)
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
        nodes_electric_data
    ) = export_cal_country(flows_all_df, target_country)
    
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
    nodes_electric_data[target_country] = nodes_electric_data


exports_all_sum.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_all_sum.xlsx")
exports_all.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_all.xlsx")
exports_H2_sum.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_H2_sum.xlsx")
exports_H2.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_H2.xlsx")
exports_within_country_H2_sum.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_H2_sum.xlsx")
exports_within_country_H2.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_H2.xlsx")
exports_within_country_electricity_H2_sum.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_electricity_H2_sum.xlsx")
exports_within_country_electricity_H2.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_electricity_H2.xlsx")
exports_within_country_electricity_sum.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_electricity_sum.xlsx")
exports_within_country_electricity.to_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\exports_within_country_electricity.xlsx")
# export nodes_electric_data to an excel file where each sheet is a country
with pd.ExcelWriter(r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022\analysis\nodes_electric_data.xlsx") as writer:
    for country, data in nodes_electric_data.items():
        data.to_excel(writer, sheet_name=country)
