import pandas as pd
import os
import plotly.graph_objects as go

# define paths ---------------------------------------------------------------
source_data_dir = r"C:\Users\daru\OneDrive - ZHAW\EDGE\data_sources\OREES//"
target_output_dir = r"availability_factors_CH_OREES//"

Mapping_nameOREES_tech = {
    "NoRoof_FreeStanding_OptiWinter": "pv_field_winter",
    "Roof_East_23deg": "pv_rooftop_east",
    "Roof_FreeStanding_OptiYear": "pv_field_year",
    "Roof_South_23deg": "pv_rooftop_south",
    "Roof_West_23deg": "pv_rooftop_west",
}

# define years ---------------------------------------------------------------
# target climate years
# I only have data for 2008 (or 2009)


# functions      -----------------------------------------------------------
def read_res_avail_factor_OREES(tech):
    """
    """
    df_data = pd.read_csv(source_data_dir + tech + ".csv", header=None)
    # assign names CH01, CH02, etc. to the columns
    df_data.columns = ["CH_" + str(i).zfill(2) for i in range(1, 7+1)]
    
    # change the index value to "t_1", "t_2", etc.
    df_data.index = ["t_" + str(i) for i in range(1, 8760+1)]

    return df_data


# if target_output_dir does not exist, create it
if not os.path.exists(target_output_dir):
    os.makedirs(target_output_dir)

avail_fact_dict = {}
for tech_orees, tech_model in Mapping_nameOREES_tech.items():
    print(tech_model)
    avail_fact_dict[tech_model] = read_res_avail_factor_OREES(tech_orees)
    avail_fact_dict[tech_model].to_csv(target_output_dir + tech_model + ".csv")

# create east + west availability factor
avail_fact_dict["pv_rooftop_east_west"] = 0.5*(avail_fact_dict["pv_rooftop_east"] + avail_fact_dict["pv_rooftop_west"])
avail_fact_dict["pv_rooftop_east_west"].to_csv(target_output_dir + "pv_rooftop_east_west.csv")


# sanity checks and plots ----------------------------------------------------
# reading data from the folder
# define subregions to plot sub_regions = [] plots all reions
# sub_regions = ["CH_01", "CH_02", "CH_03", "CH_04", "CH_05", "CH_06", "CH_07"]
sub_regions = ["CH_01",]

# read all the files in target_output_dir
avail_fact_all = pd.DataFrame()
for file in os.listdir(target_output_dir):
    if file.endswith(".csv"):
        # read the file and save it in df_temp
        temp_df = pd.read_csv(target_output_dir + file, index_col=0)

        # rename columns of temp_df to current column name + file[:-4]
        temp_df.columns = [col + "_" + file[:-4] for col in temp_df.columns]

        # concatenate df_temp to avail_fact_all
        avail_fact_all = pd.concat([avail_fact_all, temp_df], axis=1)
        # save df_temp in avail_fact_dict[file[:-4]]

# plot the availability factors ----------------------------------------------
if sub_regions == []:
    data_to_plot = avail_fact_all.copy()
else:
    # keep the columns that contain any of the elements in sub_regions
    data_to_plot = avail_fact_all.filter(regex="|".join(sub_regions))

fig = go.Figure()

# plot columns in avail_fact_all 
fig = go.Figure()
for col in data_to_plot.columns:
    fig.add_trace(go.Scatter(x=data_to_plot.index, y=data_to_plot[col], name=col))

fig.update_layout(title='Availability factors for different technologies within Switzerland',
                     xaxis_title='Time',
                     yaxis_title='Availability factor',
                     )

fig.show()

# calculate summary statistics -----------------------------------------------
summary_stats = avail_fact_all.describe()

# create a folder called stats and save the summary statistics there
if not os.path.exists(target_output_dir + "stats//"):
    os.makedirs(target_output_dir + "stats//")

summary_stats.to_csv(target_output_dir + "stats//summary_stats.csv")