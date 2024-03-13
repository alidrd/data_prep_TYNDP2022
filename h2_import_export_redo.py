"""
This script reads the excel file "220310_Updated_Electricity_Modelling_Results.xlsx" and extracts the H2 import and export data for the target years and scenarios.
The data is then saved as a csv file.
This script overwrites previous adhoc attempts to extract the data.

Previously, some of demand from different electrolysis methods yielded net demand.
In this script, the net H2 import of regions are also calculated, to be deducted from electrolysis methods demand.
"""

import pandas as pd

climate_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\TYNDP_2022//"
target_output_dir = r"inputs_to_model//"
input_dir = r"annuals_cap_dem_gen_imp//"

runyear_target_list = [2030, 2040, 2050]
weatheryear_target_list = [1995, 2008, 2009]
eu_scenario_list = ["Distributed Energy", "Global Ambition"]

Node_list_setting = [
    "CH00",
    "IT00",
    "DE00",
    # "DEKF",  # ?
    "FR00",
    "AT00",
    "DKE1",  # ?
    "DKW1",  # ?
    # "DKKF", # ?
    "BE00",
    "CZ00",
    "ES00",
    "UK00",
    "HU00",
    "LU00",
    "NL00",
    "PL00",
    "PT00",
    "SI00",
    "SK00",
    "HR00",
    "SE01",
    "SE02",
    "SE03",
    "SE04",
    "NON1",
    "NOM1",
    "NOS0",
]
# Import and trim the data ---------------------------------------------------------------------------

flows_all_df = pd.read_excel(f"{climate_data_dir}220310_Updated_Electricity_Modelling_Results.xlsx", sheet_name="Line")

# only keep these columns in the dataframe: Node/Line, Parameter, Scenario, Year, Climate Year, Value
flows_all_df = flows_all_df[["Node/Line", "Parameter", "Scenario", "Year", "Climate Year", "Value"]]

# only keep rows that have Flow (GWh) or Flow Back (GWh) in the column Parameter
flows_all_df = flows_all_df[flows_all_df["Parameter"].str.contains("Flow")]

# only keep the rows that have H2 twice in the column Node/Line
flows_h2_df = flows_all_df[flows_all_df["Node/Line"].str.count("H2") == 2]


# # only keep the rows that have the target countries
# pattern = '|'.join(Node_list_setting)
# flows_h2_df = flows_h2_df[flows_h2_df["Node/Line"].str.contains(pattern)]

# only keep the columns that have the target years
flows_h2_df = flows_h2_df[flows_h2_df["Year"].isin(runyear_target_list)]


# create column "from" and "to", where 
# the "from" is the first 4 characters of the "Node/Line" column
# the "to" is the first 4 characters of the "Node/Line" after the first "-"
flows_h2_df["from"] = flows_h2_df["Node/Line"].str[:4]
flows_h2_df["to"] = flows_h2_df["Node/Line"].str.split("-", expand=True)[1].str[:4]

# exclude rows that have similar "from" and "to"
flows_h2_df = flows_h2_df[flows_h2_df["from"] != flows_h2_df["to"]]

# for every row, if Parameter is "Flow Back (GWh)", multiply the Value by -1
flows_h2_df.loc[flows_h2_df["Parameter"] == "Flow Back (GWh)", "Value"] = flows_h2_df.loc[flows_h2_df["Parameter"] == "Flow Back (GWh)", "Value"] * -1

# for every unique node in the "from" column, regions, calculate H2 export and import
# sum export is equal to values in which each region is the "from"
# sum import is equal to values in which each region is the "to"
# the difference between the two is the net export

# create a multiiindex dataframe with region_name, H2_export, H2_import, H2_net_export
flows_h2_export_import_df = pd.DataFrame(columns=["plant_name" ,"node", "year","scenario", "weather_year", "H2_export", "H2_import", "H2_net_export", "net_demand_electrolysis"])
demand_all_df = pd.read_excel(f"{climate_data_dir}220310_Updated_Electricity_Modelling_Results.xlsx", sheet_name="Demand")
electrolysis_demand_df = pd.DataFrame(columns=["node", "year", "scenario", "weather_year", "electrolysis_demand"])
columns_electrolyzer = ["Electrolysis Config 1",  "Electrolysis Config 2",  "Electrolysis Config 3",  "Electrolysis Config 4", "Electrolysis Config 5"]


row_counter = 0
for scenario in eu_scenario_list:
    for year in runyear_target_list:
        for weather_year in weatheryear_target_list:
            # for every unique node in the "from" column, calculate H2 export and import
            for node in Node_list_setting:
                # calculate H2 export and import
                # where H2_export is the sum of all values in which the "from" is the node, and year in Year and weather_year in Climate Year
                H2_export = flows_h2_df[(flows_h2_df["from"] == node) 
                                        & (flows_h2_df["Year"] == year) 
                                        & (flows_h2_df["Scenario"] == scenario)
                                        & (flows_h2_df["Climate Year"] == weather_year)
                                        ]["Value"].sum()
                
                # where H2_import is the sum of all values in which the "to" is the node, and year in Year and weather_year in Climate Year
                H2_import = flows_h2_df[(flows_h2_df["to"] == node)
                                        & (flows_h2_df["Year"] == year) 
                                        & (flows_h2_df["Scenario"] == scenario)
                                        & (flows_h2_df["Climate Year"] == weather_year)
                                        ]["Value"].sum()

                # the difference between the two is the net export
                H2_net_export = H2_export - H2_import

                # read electrolysis demand data
                demand_electrolysis = demand_all_df[(demand_all_df["Node"].str.startswith(node)) 
                        & (demand_all_df["Year"] == year) 
                        & (demand_all_df["Scenario"] == scenario)
                        & (demand_all_df["Climate Year"] == "CY " + str(weather_year))
                        & (demand_all_df["Type_node"].isin(columns_electrolyzer))	
                        ]["Value"].sum()

                net_demand_electrolysis = demand_electrolysis + H2_net_export

                flows_h2_export_import_df.loc[row_counter, "plant_name"] = node + "_electrolyzer"
                flows_h2_export_import_df.loc[row_counter, "node"] = node
                flows_h2_export_import_df.loc[row_counter, "year"] = year
                flows_h2_export_import_df.loc[row_counter, "scenario"] = scenario.replace(" ", "_")
                flows_h2_export_import_df.loc[row_counter, "weather_year"] = weather_year
                flows_h2_export_import_df.loc[row_counter, "H2_export"] = H2_export
                flows_h2_export_import_df.loc[row_counter, "H2_import"] = H2_import
                flows_h2_export_import_df.loc[row_counter, "H2_net_export"] = H2_net_export
                flows_h2_export_import_df.loc[row_counter, "electrolysis_demand"] = demand_electrolysis
                flows_h2_export_import_df.loc[row_counter, "net_demand_electrolysis"] = net_demand_electrolysis * 1000 # convert from GWh to MWh
                row_counter += 1
    # add the results to the dataframe
flows_h2_export_import_df.to_csv(f"flows_h2_export_import_electrolysis_all_data.csv", index=False)

# only keep column net_demand_electrolysis, and pivot the dataframe based on the columns year
electrolysis_net_demand_df = flows_h2_export_import_df[["plant_name", "node", "year", "scenario", "weather_year", "net_demand_electrolysis"]].pivot(index=["plant_name", "node", "scenario", "weather_year"], columns="year", values="net_demand_electrolysis")

electrolysis_net_demand_df.to_csv(f"{target_output_dir}electrolyzer_net_demand.csv")

electrolysis_demand_df.to_clipboard(index=True, header=True)