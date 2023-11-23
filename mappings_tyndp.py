import pandas as pd

# Read in the data
mappings_df = pd.read_excel(r"C:\Users\daru\OneDrive - ZHAW\EDGE\TYNDP_2022\220310_Updated_Electricity_Modelling_Results - Kopie.xlsx", sheet_name="Nodes - Dict")

# Create a dictionary with the mappings, where the key is unique values in column Country Name and the value is all corresponding values in column Node
Map_countryname_nodes = {key: mappings_df.loc[mappings_df["Country Name"] == key, "Node"].tolist() 
                         for key in mappings_df["Country Name"].unique()}
# remove nan values from keys
Map_countryname_nodes = {k: v for k, v in Map_countryname_nodes.items() if str(k) != 'nan'}
Map_countryname_nodes["Germany"]
# ['DE00', 'DE00H2C1', 'DE00H2C2', 'DE00H2C3', 'DE00HER4', 'DE00H2R4', 'DE00H2R1', 'DE00H2MT', 'DE00RETE', 'DE00EV2W', 'DEg', 'DEgL', 'DEn', 'DEnL']

# Create a dictionary with the mappings, where the key is unique values in column Country Name and the value is all corresponding values in column Country
Map_countryname_regions = {key: list(set(mappings_df.loc[mappings_df["Country Name"] == key, "Country"].tolist())) for key in mappings_df["Country Name"].unique()}
# remove nan values from keys
Map_countryname_regions = {k: v for k, v in Map_countryname_regions.items() if str(k) != 'nan'}
Map_countryname_regions["Sweden"]
# ['SE04', 'SE01', 'SE03', 'SE00', 'SE02']

# Create a dictionary with the mappings, where the key is unique values in column Country and the value is all corresponding values in column Node
Map_region_nodes = {key: mappings_df.loc[mappings_df["Country"] == key, "Node"].tolist() for key in mappings_df["Country"].unique()}
# remove nan values from keys
Map_region_nodes = {k: v for k, v in Map_region_nodes.items() if str(k) != 'nan'}
Map_region_nodes["DE00"]
# ['DE00', 'DE00H2C1', 'DE00H2C2', 'DE00H2C3', 'DE00HER4', 'DE00H2R4', 'DE00H2R1', 'DE00H2MT', 'DE00RETE', 'DE00EV2W', 'DEKF', 'DE01', 'DE02', 'DE03', 'DE04', 'DE05', 'DE06', 'DE07']


# Crete a dictionary with the mappings, where the key is unique values in column Type and the value is all corresponding values in column Node
Map_type_nodes = {key: mappings_df.loc[mappings_df["Type"] == key, "Node"].tolist() for key in mappings_df["Type"].unique()}
# remove nan values from keys
Map_type_nodes = {k: v for k, v in Map_type_nodes.items() if str(k) != 'nan'}
#dict_keys(['Emarket', 'H-market', 'Transport', 'FIZC1', 'FIZC2', 'FIZC3', 'FIZC4', 'FIZR1', 'Prosumer', 'Imports', nan])
Map_type_nodes["H-market"]
# ['AL00H2MT', 'AT00H2MT', 'BA00H2MT', 'BE00H2MT', 'BG00H2MT', 'CH00H2MT', ...]



