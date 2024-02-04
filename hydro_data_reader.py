
# %%
# load EU hydro data from Matteo de felice and export to CSVs for model
#creates plants,waternodes, hourly inflow and storage level datasets for selected weather years
#
from numpy.core.numeric import indices
import pandas as pd
import os
import sys
current_directory = os.getcwd()
sys.path.append(current_directory + '/src')

# define paths ---------------------------------------------------------------
climate_data_dir = r"source_hydro_PECD\PECD_hydro//"
target_output_dir = r"hydro_PECD//"

# define years ---------------------------------------------------------------
# years for which capacity factor is available
PECD_data_years_list = [2030, 2025]

# target climate years
climate_years_list = [2008, 2007, 1995]


# define mappings ------------------------------------------------------------
# technology mapping
technology_dict = {"Reservoir"                :"dam",
                   "Run-of-River and pondage"  :"ror",
                   "Pump Storage - Open Loop"  :"psp_open",
                   "Pump Storage - Closed Loop":"psp_closed",
}
map_zone = {'AT00':'AT00','BE00':'BE00','CZ00':'CZ00','DE00':'DE00','ES00':'ES00','FR00':'FR00','HR00':'HR00','HU00':'HU00','ITCN':'ITCN','ITCS':'ITCS','ITN1':'ITN1','ITS1':'ITS1','ITSA':'ITSA','ITSI':'ITSI','LUG1':'LU00','LUV1':'LU00','NL00':'NL00','NOM1':'NOM1','NON1':'NON1','NOS0':'NOS0','PL00':'PL00','PT00':'PT00','SE01':'SE01','SE02':'SE02','SE03':'SE03','SE04':'SE04','SI00':'SI00','SK00':'SK00','UK00':'UK00','CH00':'CH00'}

# %%
# Load capacities data
df_capacities = pd.read_csv(climate_data_dir+"PECD-hydro-capacities.csv")

# %%
# Create separate df_plants dataframe (should replace other hydro plant data - apart from CH)
df_plants = df_capacities[(df_capacities.variable == "Total turbining capacity (MW)") | 
                          (df_capacities.variable == 'Total pumping capacity (MW)')].copy()
df_plants = pd.pivot_table(df_plants,index=['zone','type'], columns='variable',values='value').reset_index()
df_plants["tech"] = df_plants.type.map(technology_dict)
df_plants = df_plants[df_plants["tech"]!="RoR"]
df_plants["zone"] = df_plants.zone.map(map_zone)
df_plants = df_plants.groupby(['tech','zone']).sum().reset_index()
df_plants["index"] = df_plants.zone + "_" + df_plants.tech
df_plants['g_max'] = df_plants['Total turbining capacity (MW)']
df_plants['mc'] = 0
df_plants['p_max'] = df_plants['Total pumping capacity (MW)']
df_plants['node'] = df_plants['zone']
df_plants['eta'] = 1
df_plants['eta_pump'] = 0.75
df_plants['upper_node'] = df_plants["index"] + "_upper_node"
df_plants['lower_node'] = df_plants["index"] + "_lower_node"
df_plants["plant_type"] = "hydro"
df_plants = df_plants[["index","node","zone","plant_type","tech","upper_node","lower_node","eta","eta_pump"]]
df_plants.to_csv(target_output_dir + "plants_hydro_EU.csv", encoding="utf-8", index=False)

df_plants.tech.unique()

# %%
# Create separate df_waternodes dataframe (should replace other waternode data - apart from CH)
df_waternodes = df_capacities[(df_capacities.variable == "Reservoir capacity (GWh)") |
                              (df_capacities.variable == "Cumulated (upper or head) reservoir capacity (GWh)")]
df_waternodes = pd.pivot_table(df_waternodes,index=['zone','type'], columns='variable',values='value').reset_index()
#check if both exist or its just two different titles for the same thing
df_waternodes[(df_waternodes["Cumulated (upper or head) reservoir capacity (GWh)"]>0) & 
               (df_waternodes["Reservoir capacity (GWh)"]>0)] 
df_waternodes = df_waternodes.fillna(0)
df_waternodes["zone"] = df_waternodes.zone.map(map_zone)
df_waternodes = df_waternodes.groupby(['zone','type']).sum().reset_index()
df_waternodes = df_waternodes.dropna()
df_waternodes['stor_max'] = df_waternodes["Cumulated (upper or head) reservoir capacity (GWh)"] + df_waternodes["Reservoir capacity (GWh)"]
#convert GWh to MWh
df_waternodes['stor_max'] = df_waternodes['stor_max'] *1000
df_waternodes["tech"] = df_waternodes.type.map(technology_dict)
df_waternodes["index"] = df_waternodes.zone + "_" + df_waternodes.tech + "_upper_node"
df_waternodes["type"] = "upper"
#change tech for no from psp_open to dam, SI psp_open to psp_closed
Norway = ['NOM1','NON1','NOS0']
for i in Norway:
    df_waternodes.loc[(df_waternodes.zone==i) & (df_waternodes.tech=='Dam'),'stor_max'] = df_waternodes.loc[(df_waternodes.zone==i) & (df_waternodes.tech=='PSP_Open'),'stor_max'].values
    df_waternodes.loc[(df_waternodes.zone==i) & (df_waternodes.tech=='PSP_Open'),'stor_max'] = 0
df_waternodes.loc[(df_waternodes.zone=='SI00') & (df_waternodes.tech=='PSP_Closed'),'stor_max'] = df_waternodes.loc[(df_waternodes.zone=='SI00') & (df_waternodes.tech=='PSP_Open'),'stor_max'].values
df_waternodes.loc[(df_waternodes.zone=='SI00') & (df_waternodes.tech=='PSP_Open'),'stor_max'] = 0
df_waternodes_lower = df_waternodes.copy()
df_waternodes_lower["index"] = df_waternodes.zone + "_" + df_waternodes.tech + "_lower_node"
df_waternodes_lower["type"] = "lower"
concatenated_df = pd.concat([df_waternodes, df_waternodes_lower])
df_waternodes["lower_node"]=""
df_waternodes["planttype"] = df_waternodes.tech
df_waternodes["country"]=df_waternodes.zone.str[:2]
df_waternodes.head()
df_waternodes = df_waternodes[["index","lower_node","stor_max","zone","type","planttype","country"]]
df_waternodes.to_csv(target_output_dir + "waternodes_EU.csv", encoding="utf-8", index=False)

# %%
# Load waternodes inflow data
df_waternodes_inflow = pd.read_csv(climate_data_dir+"PECD-hydro-weekly-inflows.csv")
df_waternodes_inflow['week'] = 'w'+df_waternodes_inflow['week'].astype(str)
df_waternodes_inflow_dam = df_waternodes_inflow[df_waternodes_inflow["Cumulated inflow into reservoirs per week in GWh"] > 0].copy()
df_waternodes_inflow_dam["MWh"] =  df_waternodes_inflow_dam['Cumulated inflow into reservoirs per week in GWh'] * 1000 / (7*24)
df_waternodes_inflow_dam["tech"] = "Dam"
df_waternodes_inflow_dam = df_waternodes_inflow_dam[["zone","week","year","tech","MWh"]]
#split by technologies and merge again
df_waternodes_inflow_psp_open = df_waternodes_inflow[df_waternodes_inflow["Cumulated NATURAL inflow into the pump-storage reservoirs per week in GWh"] > 0].copy()
df_waternodes_inflow_psp_open["MWh"] =  df_waternodes_inflow_psp_open['Cumulated NATURAL inflow into the pump-storage reservoirs per week in GWh'] * 1000 / (7*24)
df_waternodes_inflow_psp_open["tech"] = "PSP_Open"
df_waternodes_inflow_psp_open = df_waternodes_inflow_psp_open[["zone","week","year","tech","MWh"]]

#change tech for no from psp_open to dam
Norway = ['NOM1','NON1','NOS0']
for i in Norway:
    df_waternodes_inflow_psp_open.loc[(df_waternodes_inflow_psp_open.zone==i) & (df_waternodes_inflow_psp_open.tech=='PSP_Open'),'tech'] = 'Dam'

df_waternodes_inflow = pd.concat([df_waternodes_inflow_dam, df_waternodes_inflow_psp_open])
df_waternodes_inflow["index"] = df_waternodes_inflow.zone + "_" + df_waternodes_inflow.tech + "_upper_node"

df_waternodes_inflow.head()

#now we separate into the three weather years (more can be selected at the beginning of this file)
for year in climate_years_list:
    df_temp = pd.DataFrame()
    df_temp = df_waternodes_inflow[df_waternodes_inflow['year'] == year]
    df_temp = df_temp[['index','week','MWh']]
    #export
    df_temp.to_csv(target_output_dir + "waternodes_inflow_" + str(year) + "_EU.csv", encoding="utf-8", index=False)

# %%
# Load waternodes level data
df_waternodes_level = pd.read_csv(climate_data_dir+"PECD-hydro-weekly-reservoir-levels.csv")
df_waternodes_level['week'] = 'w'+df_waternodes_level['week'].astype(str)
df_waternodes_level = df_waternodes_level.rename(columns={'Reservoir levels at beginning of each week (ratio) 0<=x<=1.0':'level','Minimum Reservoir levels at beginning of each week (ratio) 0<=x<=1.0':'level_min','Maximum Reservoir level at beginning of each week (ratio) 0<=x<=1.0':'level_max'})
df_waternodes_level['level'] = df_waternodes_level['level'].fillna((df_waternodes_level['level_min']+df_waternodes_level['level_max'])/2)
df_waternodes_level.head()

# #we use 2016 levels for 2017
# df_waternodes_level.year[((df_waternodes_level.zone=="AT00") & (df_waternodes_level.year==2017))]=0000
# df_waternodes_level.year[((df_waternodes_level.zone=="AT00") & (df_waternodes_level.year==2016))]=2017

#now we separate into the three weather years (more can be selected at the beginning of this file)
for year in climate_years_list:
    df_temp = pd.DataFrame()
    df_temp = df_waternodes_level[df_waternodes_level['year'] == year]
    df_temp = df_temp[['zone','week','level']]
    #export
    df_temp.to_csv(target_output_dir + "waternodes_level_" + str(year) + "_EU.csv", encoding="utf-8", index=False)


#we also load RoR daily generation from PECD
df_gen_ror = pd.read_csv(climate_data_dir+"PECD-hydro-daily-ror-generation.csv")
df_gen_ror['MWh'] = df_gen_ror["Run of River Hydro Generation in GWh per day"] * 1000 / 24
df_gen_ror['zone'] = df_gen_ror['zone'].map(map_zone) 
df_gen_ror = df_gen_ror.dropna()
df_gen_ror = df_gen_ror.groupby(['zone','year','Day']).sum().reset_index()
df_gen_ror.head()

for year in climate_years_list:
    df_temp = pd.DataFrame()
    df_temp = df_gen_ror[df_gen_ror['year'] == year]
    df_temp = df_temp[['zone','Day','MWh']]
    #export
    df_temp.to_csv(target_output_dir + "ror_inflow_hourly_" + str(year) + "_EU.csv", encoding="utf-8", index=False)
