import pandas as pd

"""Input"""
file_path = "C:\\Users\\avanliede\\Documents\\02_Projects\\01_Nexus-e\\02_Input\\TYNDP_2022\\TYNDP_2022_DataCollection_Main.xlsx"

"""Load data"""
df_import_export = pd.read_excel(file_path, sheet_name='Line', header=0, index_col=0)

""""Modify data structure"""
# Separate from and to node code
df_import_export["Node_from"] = [x[0:4] for x in list(df_import_export.index)]
df_import_export["Node_to"] = [x[x.find("-")+1:x.find("-")+5] for x in list(df_import_export.index)]
df_import_export["Country_from"] = [x[0:2] for x in list(df_import_export.index)]
df_import_export["Country_to"] = [x[x.find("-")+1:x.find("-")+3] for x in list(df_import_export.index)]
df_import_export["Additional from"] = [x[4:x.find("-")] for x in list(df_import_export.index)]
df_import_export["Additional to"] = [x[x.find("-")+5:] for x in list(df_import_export.index)]

# Understand what the options for each column are
set_Parameter = set(df_import_export["Parameter"])
set_Category = set(df_import_export["Category"])
set_Case = set([x for x in df_import_export["Case"] if x is not None])
set_Simulation_type = set(df_import_export["Simulation_type"])
set_Sector = set(df_import_export["Sector"])


"""Functions"""
def get_imports_exports(df_CH, df_AT, df_DE, df_FR, df_IT):
    # Initialize dictionaries
    im_ex = {}
    imports_exports_df = {}
    imports_exports_excl_modeled = {}
    df_dict = {"CH": df_CH,
               "AT": df_AT,
               "DE": df_DE,
               "FR": df_FR,
               "IT": df_IT}

    for country, df in df_dict.items():
        # Main country code
        # country_code = country + "00"

        # Save imports-exports per country
        imports_exports_df[country] = {}
        imports_exports_df[country]["import"] = pd.concat(
            [df[(df["Parameter"] == "Flow (GWh)")
                & (df["Country_to"] == country)
                & (df["Country_from"] != df["Country_to"])],
             df[(df["Parameter"] == "Flow Back (GWh)")
                & (df["Country_from"] == country)
                & (df["Country_from"] != df["Country_to"])],
             df[(df["Parameter"] == "Flow (GWh)")
                & (df["Additional to"] == "")
                & (df["Country_from"] == df["Country_to"])],
             df[(df["Parameter"] == "Flow Back (GWh)")
                & (df["Additional from"] == "")
                & (df["Country_from"] == df["Country_to"])]])
        imports_exports_df[country]["export"] = pd.concat(
            [df[(df["Parameter"] == "Flow (GWh)")
                & (df["Country_from"] == country)
                & (df["Country_from"] != df["Country_to"])],
             df[(df["Parameter"] == "Flow Back (GWh)")
                & (df["Country_to"] == country)
                & (df["Country_from"] != df["Country_to"])],
             df[(df["Parameter"] == "Flow (GWh)")
                & (df["Additional from"] == "")
                & (df["Country_from"] == df["Country_to"])],
             df[(df["Parameter"] == "Flow Back (GWh)")
                & (df["Additional to"] == "")
                & (df["Country_from"] == df["Country_to"])]
             ])

        # All imports/exports
        import_df = sum(imports_exports_df[country]["import"]["Value"])
        export_df = sum(imports_exports_df[country]["export"]["Value"])
        net_import = import_df - export_df  # GWh

        # Imports/exports excluding those from-to any of the modeled countries
        import_df_excl_modeled = sum(df[(df["Parameter"] == "Flow (GWh)")
                                        & (df["Country_to"] == country)
                                        & (~df["Country_from"].isin(df_dict.keys()))]["Value"]) \
                                 + sum(df[(df["Parameter"] == "Flow Back (GWh)")
                                          & (df["Country_from"] == country)
                                          & (~df["Country_to"].isin(df_dict.keys()))]["Value"])
        export_df_excl_modeled = sum(df[(df["Parameter"] == "Flow (GWh)")
                                        & (df["Country_from"] == country)
                                        & (~df["Country_to"].isin(df_dict.keys()))]["Value"]) \
                                 + sum(df[(df["Parameter"] == "Flow Back (GWh)")
                                          & (df["Country_to"] == country)
                                          & (~df["Country_from"].isin(df_dict.keys()))]["Value"])
        net_import_excl_modeled = import_df_excl_modeled - export_df_excl_modeled  # GWh

        im_ex[country] = {
            "import": import_df,
            "export": export_df,
            "net_import": net_import
        }
        imports_exports_excl_modeled[country] = {
            "import": import_df_excl_modeled,
            "export": export_df_excl_modeled,
            "net_import": net_import_excl_modeled
        }
    return im_ex, imports_exports_excl_modeled, imports_exports_df

def get_NTC(df, country):
    # Create an empty dataframe
    df_NTC = pd.DataFrame({
        "Country_from": [],
        "Country_to": [],
        "Parameter": [],
        "Value": []
    })

    # Change rows, to have "country_from" always equal to the country the df is referring to
    for idx, row in df.iterrows():
        new_row = {}
        if row["Country_from"] != country:
            # Invert order
            new_row["Country_to"] = row["Country_from"]
            new_row["Country_from"] = country
            if row["Parameter"] == "Export Capacity (MW)":
                new_row["Parameter"] = "Import Capacity (MW)"
            elif row["Parameter"] == "Import Capacity (MW)":
                new_row["Parameter"] = "Export Capacity (MW)"
            new_row["Value"] = - row["Value"]
        else:
            # Keep it as it is
            new_row["Country_from"] = row["Country_from"]
            new_row["Country_to"] = row["Country_to"]
            new_row["Parameter"] = row["Parameter"]
            new_row["Value"] = row["Value"]

        # Append new row
        df_NTC = df_NTC.append(new_row, ignore_index=True)

    # Group results
    df_NTC_grouped = df_NTC.groupby(['Country_from', 'Country_to', 'Parameter'])['Value'].sum().reset_index()

    return df_NTC_grouped

# Select flow parameter from the df
df_import_export_capacity = df_import_export[df_import_export["Parameter"].isin(["Import Capacity (MW)", "Export Capacity (MW)"])]

# Initialize dictionaries with the results
im_ex_df = pd.DataFrame({
    "Scenario": [],
    "Year": [],
    "Climate Year": [],
    "Country_from": [],
    "Country_to": [],
    "Parameter": [],
    'Value': []
})

# Iterate through scenarios
for scenario in ["Global Ambition", "Distributed Energy"]:
    # Select the scenario
    df_import_export_capacity_scenario = df_import_export_capacity[df_import_export_capacity["Scenario"] == scenario]

    # Iterate through years
    for year in [2050, 2030, 2040]:
        # Select the scenario year
        df_import_export_capacity_scenario_year = df_import_export_capacity_scenario[df_import_export_capacity_scenario["Year"] == year]

        # Iterate through climate years
        for cy in [1995, 2008, 2009]:
            # Select climate year
            df_import_export_capacity_scenario_year_cy = df_import_export_capacity_scenario_year[df_import_export_capacity_scenario_year["Climate Year"] == cy]

            ### All import/export entries for each country
            df_import_export_capacity_scenario_year_cy_CH = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("CH")]
            df_import_export_capacity_scenario_year_cy_AT = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("AT")]
            df_import_export_capacity_scenario_year_cy_DE = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("DE")]
            df_import_export_capacity_scenario_year_cy_FR = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("FR")]
            df_import_export_capacity_scenario_year_cy_IT = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("IT")]
            df_import_export_capacity_scenario_year_cy_LU = df_import_export_capacity_scenario_year_cy[df_import_export_capacity_scenario_year_cy.index.str.contains("LU")]

            ### Only interational flows to/from country's main node (one sided)
            df_im_ex_capacity_sc_y_cy_CH_main_node_intercountry = df_import_export_capacity_scenario_year_cy_CH[
                ((df_import_export_capacity_scenario_year_cy_CH["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_CH["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_CH["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_CH["Country_to"])]
            df_im_ex_capacity_sc_y_cy_AT_main_node_intercountry = df_import_export_capacity_scenario_year_cy_AT[
                ((df_import_export_capacity_scenario_year_cy_AT["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_AT["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_AT["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_AT["Country_to"])]
            df_im_ex_capacity_sc_y_cy_DE_main_node_intercountry = df_import_export_capacity_scenario_year_cy_DE[
                ((df_import_export_capacity_scenario_year_cy_DE["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_DE["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_DE["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_DE["Country_to"])]
            df_im_ex_capacity_sc_y_cy_FR_main_node_intercountry = df_import_export_capacity_scenario_year_cy_FR[
                ((df_import_export_capacity_scenario_year_cy_FR["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_FR["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_FR["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_FR["Country_to"])]
            df_im_ex_capacity_sc_y_cy_IT_main_node_intercountry = df_import_export_capacity_scenario_year_cy_IT[
                ((df_import_export_capacity_scenario_year_cy_IT["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_IT["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_IT["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_IT["Country_to"])]
            df_im_ex_capacity_sc_y_cy_LU_main_node_intercountry = df_import_export_capacity_scenario_year_cy_LU[
                ((df_import_export_capacity_scenario_year_cy_LU["Additional from"] == "")
                 | (df_import_export_capacity_scenario_year_cy_LU["Additional to"] == ""))
                & (df_import_export_capacity_scenario_year_cy_LU["Country_from"] !=
                   df_import_export_capacity_scenario_year_cy_LU["Country_to"])]

            # Get NTC values grouped
            df_CH_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_CH_main_node_intercountry, "CH")
            df_AT_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_AT_main_node_intercountry, "AT")
            df_DE_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_DE_main_node_intercountry, "DE")
            df_FR_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_FR_main_node_intercountry, "FR")
            df_IT_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_IT_main_node_intercountry, "IT")
            df_LU_NTC = get_NTC(df_im_ex_capacity_sc_y_cy_LU_main_node_intercountry, "LU")

            # Concatenate all data frames
            df_all_NTC = pd.concat([df_CH_NTC, df_AT_NTC, df_DE_NTC, df_FR_NTC, df_IT_NTC, df_LU_NTC], ignore_index=True)

            # Add missing columns
            df_all_NTC["Scenario"] = scenario
            df_all_NTC["Year"] = year
            df_all_NTC["Climate Year"] = cy

            # Append this data frame to the overarching one
            im_ex_df = pd.concat([im_ex_df, df_all_NTC], ignore_index=True)

# Save dataframe to excel
im_ex_df.to_excel('NTC_all.xlsx', index=False)

print("Done!")

