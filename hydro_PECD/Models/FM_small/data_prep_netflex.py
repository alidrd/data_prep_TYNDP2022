import pandas as pd

# define the parameters ---------------------------------------------------------------------------------------------------
kw_mw_conversion_factor = 0.001  # 1 kW = 0.001 MW
ev_charging_capacity = 11 * kw_mw_conversion_factor  # MWh
ev_battery_capacity = 50 * kw_mw_conversion_factor  # MWh
ev_charging_efficiency_roundtrip = 0.9  # 90%

battery_charging_efficiency_roundtrip = 0.9  # 90%
battery_charging_capacity = 3 * kw_mw_conversion_factor  # MWh
battery_battery_capacity_ratio_to_PV_capacity = 1.5  # ratio to PV capacity # The battery capacity is dimensioned with a factor of 1.5 in relation to the PV peak power.

pv_max_capacity = 4.44 * kw_mw_conversion_factor  # MW
# hp_capacity = 4.1350228 # max electric consumption in the dataset among 300 consumers was this. I didn't use it.

flex_duartion = {
    "hp": 6,
    "v1g": 168,
}  # the duration of flexibility for each asset in hours

rounding_digits = 10  # round the values in the dataframe to 7 decimal places
file_dir = "C://Users//darali00//switchdrive//EWG//felxibility_modelling//scenario10_calibration_profiles_kW_component.csv"
# file_dir = "C://Users//alida//switchdrive//EWG//felxibility_modelling//scenario10_calibration_profiles_kW_component.csv"
# --------------------------------------------------------------------------------------------------------------------------
# Read NETFLEX data---------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------
# read the csv file as a dataframe
df = pd.read_csv(file_dir, header=0, index_col=0)
df.columns = df.columns.str.replace("_hh", "_fixed")
df.columns = df.columns.str.replace("_ev", "_v1g")
df = df * kw_mw_conversion_factor  # convert the values from KW to MW
df = df.round(rounding_digits)  # round the values in the dataframe to rounding_digits

# --------------------------------------------------------------------------------------------------------------------------
# reorganize the dataframe -------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------
# Get column names and obtain consumer names
column_names = df.columns.tolist()
# create a list of consumers by creating a list of the first part of the column names.
consumer_names = []
for column_name in column_names:
    consumer_name = column_name.split("_")[0]
    consumer_names.append(consumer_name)

consumer_names = list(
    set(consumer_names)
)  # remove the duplicates from the list of consumers and sort

# --------------------------------------------------------
# create a dictionary with the consumer name as the key and the value is a dictionary with the following keys: optimization, node, type, and assets. Other data will be added later.
consumer_timeseries = {}
for consumer in df.columns.tolist():
    consumer_id = consumer.split("_")[0]

    if (
        consumer_id not in consumer_timeseries.keys()
    ):  # if consumer_timeseries[consumer_id] does not exist, create consumer_timeseries[consumer_id]= {}
        consumer_timeseries[consumer_id] = {}
    consumer_timeseries[consumer_id][
        "optimization"
    ] = "minimize_cost"  # for every consumer in consumer_timeseries, add a new key "optimization" with value "cost_minimization"
    consumer_timeseries[consumer_id]["node"] = "CH00"
    consumer_timeseries[consumer_id]["type"] = consumer.split("_")[1]
    consumer_timeseries[consumer_id]["load_profile_index"] = consumer.split("_")[2]

    if (
        not "assets" in consumer_timeseries[consumer_id].keys()
    ):  # if consumer_timeseries[consumer_id]["assets"] has some values in it, append the new asset to the list of assets
        consumer_timeseries[consumer_id]["assets"] = {}
    if "list" in consumer_timeseries[consumer_id]["assets"].keys():
        consumer_timeseries[consumer_id]["assets"]["list"].append(
            consumer.split("_")[3] + "_" + consumer_id
        )
    else:  # if consumer_timeseries[consumer_id]["assets"] is empty, create consumer_timeseries[consumer_id]["assets"]["list"] = []
        consumer_timeseries[consumer_id]["assets"]["list"] = []
        consumer_timeseries[consumer_id]["assets"]["list"].append(
            consumer.split("_")[3] + "_" + consumer_id
        )
        if consumer_timeseries[consumer_id]["type"] in [
            "type8",
            "type10",
            "type11",
            "type12",
        ]:
            consumer_timeseries[consumer_id]["assets"]["list"].append(
                "bt_" + consumer_id
            )


# --------------------------------------------------------
# for consumers in consumer_timeseries, read time series data for the available assets from the dataframe.
for consumer, consumer_data in consumer_timeseries.items():
    assets = consumer_data["assets"]["list"]
    consumer_type = consumer_data["type"]
    load_profile_index = consumer_data["load_profile_index"]
    # consumer_timeseries[consumer]["asset"]["asset_time_series"] = {}
    for asset in assets:
        if (
            asset.split("_")[0] != "bt"
        ):  # if the asset is not a battery, for which time series are not available/needed
            consumer_timeseries[consumer]["assets"][asset] = {}
            target_column = (
                f"{consumer}_{consumer_type}_{load_profile_index}_{asset.split('_')[0]}"
            )
            # Save the values in df[target_column] as a dictionary in consumer_timeseries[consumer]["asset_time_series"][asset]
            consumer_timeseries[consumer]["assets"][asset]["asset_time_series"] = {
                f"t_{i+1}": value for i, value in enumerate(df[target_column])
            }

# print some sample data
consumer_timeseries["ID237"]["type"]
consumer_timeseries["ID237"]["load_profile_index"]
consumer_timeseries["ID237"]["assets"]["list"]
consumer_timeseries["ID237"]["assets"]["v1g_ID237"]["asset_time_series"]
consumer_timeseries["ID237"]["assets"]["fixed_ID237"]["asset_time_series"]["t_1"]


# --------------------------------------------------------
# import flexiblity and capacity data


def calculate_energy_flexibility_capacity(consumer_timeseries, flex_duartion):
    """
    This function calculates the flexibility of the assets in the consumer_timeseries dictionary. The flexibility is calculated for the assets in the flex_duartion dictionary.
    The flex_duartion dictionary has the asset name as the key and the flexibility duration in hours as the value. For example, flex_duartion = {"hp": 4, "v1g": 24} means that the flexibility of the hp asset is 4 hours and the flexibility of the ev asset is 24 hours.
    The maximum demand is also set here. For heat pumps, the maximum demand is the maximum value of the asset time series. For EVs, it is 11 KW as defined in ev_charging_capacity.
    The function returns the consumer_timeseries dictionary with the flexibility of the assets added to it.
    Input:
        consumer_timeseries: a dictionary with previous data of consumers (including assets and time series of consumption)
        flex_duartion: a dictionary with the asset name as the key that shows for windos of how many hours the assets are flexible in shifting their load
    Output:
        consumer_timeseries: a dictionary with the "energy", "time_horizon", "max_demand", "battery_size", "charging_efficiency_roundtrip" and "max_gen" of the assets added to it. e.g. consumer_timeseries["ID237"]["assets"]["hp"]["time_horizon"]=[(1, 4), (5, 8), (9, 12),...] and  consumer_timeseries["ID237"]["assets"]["hp_ID237"]["energy"]=[1.8017731, 3.5919, 3.4730856

    """
    for consumer, consumer_data in consumer_timeseries.items():
        assets = consumer_data["assets"]["list"]

        for asset in assets:
            asset_type = asset.split("_")[0]
            if (
                asset_type != "bt"
            ):  # bateries are processed separately, becasue different parameters are needed
                consumer_data["assets"][asset]["time_horizon"] = []
                consumer_data["assets"][asset]["energy"] = []
                if asset_type in flex_duartion.keys():
                    for i in range(0, 8760-1, flex_duartion[asset_type]):
                        # print(i)
                        # print(i + flex_duartion[asset_type])
                        if i + flex_duartion[asset_type] <= 8760:
                            consumer_data["assets"][asset]["time_horizon"].append(
                               (i + 1, i + flex_duartion[asset_type])
                            )
                            consumer_data["assets"][asset]["energy"].append(
                                sum(
                                    consumer_data["assets"][asset]["asset_time_series"][
                                        f"t_{k+1}"
                                    ]
                                    for k in range(i, i + flex_duartion[asset_type])
                                )
                            )
                        else:  
                            consumer_data["assets"][asset]["time_horizon"].append(
                               (i + 1, 8760)
                            )
                            consumer_data["assets"][asset]["energy"].append(
                                sum(
                                    consumer_data["assets"][asset]["asset_time_series"][
                                        f"t_{k+1}"
                                    ]
                                    for k in range(i, 8760)
                                )
                            )
                if asset_type == "hp":
                    consumer_data["assets"][asset]["max_demand"] = max(
                        consumer_data["assets"][asset]["asset_time_series"].values()
                    )
                if asset_type == "v1g":
                    consumer_data["assets"][asset]["max_demand"] = ev_charging_capacity
                    consumer_data["assets"][asset]["battery_size"] = ev_battery_capacity
                    consumer_data["assets"][asset][
                        "charging_efficiency_roundtrip"
                    ] = ev_charging_efficiency_roundtrip
                if asset_type == "pv":
                    consumer_data["assets"][asset]["max_gen"] = pv_max_capacity
            elif asset_type == "bt":
                consumer_data["assets"][asset] = {}
                consumer_data["assets"][asset]["max_demand"] = battery_charging_capacity
                consumer_data["assets"][asset]["battery_size"] = (
                    battery_battery_capacity_ratio_to_PV_capacity * pv_max_capacity
                )  # The battery capacity is dimensioned with a factor of 1.5 in relation to the PV peak power.
                consumer_data["assets"][asset][
                    "charging_efficiency_roundtrip"
                ] = battery_charging_efficiency_roundtrip

    return consumer_timeseries


consumer_timeseries = calculate_energy_flexibility_capacity(
    consumer_timeseries, flex_duartion
)
# print some sample data
consumer_timeseries["ID237"]["assets"]["hp_ID237"]["time_horizon"]
consumer_timeseries["ID237"]["assets"]["hp_ID237"]["energy"]
consumer_timeseries["ID237"]["assets"]["hp_ID237"]["max_demand"]
consumer_timeseries["ID238"]["assets"]["hp_ID238"]["max_demand"]
consumer_timeseries["ID237"]["assets"]["hp_ID237"]["time_horizon"][3]
consumer_timeseries["ID237"]["assets"]["hp_ID237"]["energy"][3]
consumer_timeseries["ID237"]["assets"]["v1g_ID237"]["time_horizon"]
consumer_timeseries["ID237"]["assets"]["v1g_ID237"]["energy"]
consumer_timeseries["ID300"]["assets"]["bt_ID300"]["max_demand"]


# --------------------------------------------------------------------------------------------------------------------------
# Export data to json files ------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------

# export consumer_timeseries for each consumer as a json file
import json

for consumer in consumer_timeseries.keys():
    with open("input/consumers/" + consumer + ".json", "w") as f:
        json.dump(consumer_timeseries[consumer], f, indent=4)


# # # #-------------------------------------------------------------------------------------------------------------------------------------------------------------
# # # #-------------------------------------------------------------------------------------------------------------------------------------------------------------
# # # #--------------------------------------------------------- CODE BELOW DOES NOT WORK RIGHT NOW ----------------------------------------------------------------
# # # #--------------------------------------------------------- Summerizing and checking the data -----------------------------------------------------------------
# # # #-------------------------------------------------------------------------------------------------------------------------------------------------------------
# # # #----------------------------------------------------This is to be run for double checking purposes ----------------------------------------------------------
# # # #-------------------------------------------------------------------------------------------------------------------------------------------------------------
# # # #-------------------------------------------------------------------------------------------------------------------------------------------------------------
# # barely documented code below. This is to be run for double checking purposes. It is not necessary for the main code to run.
# # count the number of 'fixed', 'hp', 'ev', 'pv' occourances in the "assets" in consumer_timeseries.................................................
# fixed_count = 0
# hp_count = 0
# ev_count = 0
# pv_count = 0
# for consumer in consumer_timeseries.keys():
#     for asset in consumer_timeseries[consumer]["assets"]:
#         if "fixed" in asset:
#             fixed_count += 1
#         if "hp" in asset:
#             hp_count += 1
#         if "v1g" in asset:
#             ev_count += 1
#         if "pv" in asset:
#             pv_count += 1

# print("Number of consumers: ", len(consumer_timeseries.keys()))
# print("Number of assets: ", fixed_count+hp_count+ev_count+pv_count)
# print("Number of fixed assets: ", fixed_count)
# print("Number of hp assets: ", hp_count)
# print("Number of ev assets: ", ev_count)
# print("Number of pv assets: ", pv_count)  # 67% of the consumers (201) have  pv assets in 2050 - ticked

# # sum the consumptions of all the assets in each consumer --------------------------------------------------------------------------------------------
# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["net_consumption"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["net_consumption"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             consumer_timeseries[consumer]["net_consumption"][i] += consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]


# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["positive_consumption"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["positive_consumption"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             if asset != "pv_"+consumer:
#                 consumer_timeseries[consumer]["positive_consumption"][i] += consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]

# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["pv_pos"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["pv_pos"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             if asset == "pv_"+consumer:
#                 consumer_timeseries[consumer]["pv_pos"][i] += -consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]


# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["fixedxed_pos"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixedxedxed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["fixedxed_pos"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             if asset == "fixed_"+consumer:
#                 consumer_timeseries[consumer]["fixed_pos"][i] += consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]


# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["ev_pos"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["ev_pos"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             if asset == "ev_"+consumer:
#                 consumer_timeseries[consumer]["ev_pos"][i] += consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]

# for consumer in consumer_timeseries.keys():
#     consumer_timeseries[consumer]["hp_pos"] = []
#     for i in range(len(consumer_timeseries[consumer]["assets"]["fixed_"+consumer]["asset_time_series"])):
#         consumer_timeseries[consumer]["hp_pos"].append(0)
#         for asset in consumer_timeseries[consumer]["assets"]["list"]:
#             if asset == "hp_"+consumer:
#                 consumer_timeseries[consumer]["hp_pos"][i] += consumer_timeseries[consumer]["assets"][asset]["asset_time_series"]["t_" + str(i+1)]


# # # things to plot
# plot_item = "net_consumption"
# # plot_item = "positive_consumption"
# # plot_item = "pv_pos"
# # plot_item = "fixed_pos"
# # plot_item = "ev_pos"
# # plot_item = "hp_pos"

# # find the maximum value for all consumers in the plot_item+consumer_id
# max_consumption_series = []
# for consumer in consumer_timeseries.keys():
#     max_consumption_series.append(max(consumer_timeseries[consumer][plot_item]))

# #plot max_consumption_series in plotly
# import plotly.graph_objects as go
# import numpy as np
# import plotly.io as pio
# pio.renderers.default = "browser"
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=np.arange(0,len(max_consumption_series),1), y=max_consumption_series, mode='lines', name=plot_item))
# fig.update_layout(title="Max generation/demand for  " + plot_item +" for all consumers")
# fig.show()

# # plot the net consumption of N'th consumer using plotly
# import plotly.graph_objects as go
# import numpy as np
# import plotly.io as pio
# pio.renderers.default = "browser"
# consumer = "ID272"
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=np.arange(0,8760,1), y=consumer_timeseries[consumer][plot_item], mode='lines', name=plot_item))
# fig.update_layout(title="For the given asset " + plot_item +" and consumer " + consumer + ": max_consumption: "+str(max(consumer_timeseries[consumer][plot_item]))+" sum_consumption: "+str(sum(consumer_timeseries[consumer][plot_item])))
# fig.show()

# # plot all sorts of consumptions of N'th consumer using plotly --------------------------------------------------------------------------------------------
# consumer = "ID272"
# fig = go.Figure()
# for plot_item in ["positive_consumption", "pv_pos", "fixed_pos", "ev_pos", "hp_pos"]:
#     fig.add_trace(go.Scatter(x=np.arange(0,8760,1), y=consumer_timeseries[consumer][plot_item], mode='lines', name=plot_item))
# fig.update_layout(title="sum consumption/generation for consumer " + consumer)
# fig.show()

# # plot sum net consumption of all consumers per type of asset using plotly--------------------------------------------------------------------------------------------
# fig = go.Figure()
# for plot_item in ["positive_consumption", "pv_pos", "fixed_pos", "ev_pos", "hp_pos"]:
#     sum_consumption = []
#     for consumer in consumer_timeseries.keys():
#         sum_consumption.append(sum(consumer_timeseries[consumer][plot_item]))
#     fig.add_trace(go.Scatter(x=np.arange(0,8760,1), y=sum_consumption, mode='lines', name=plot_item))
# # print the max and sum consumption as the title of the plot
# fig.update_layout(title="sum consumption/generation per consumer")
# fig.update_xaxes(title_text="consumr ID")
# fig.show()


# # plot time series of consumption of assets for consumers in list target_consumer_to_plot using plotly--------------------------------------------------------------------------------------------
# target_consumer_to_plot = ["ID" + str(i) for i in range(207, 210)]
# fig = go.Figure()
# for consumer in target_consumer_to_plot:
#     for plot_item in ["positive_consumption", "pv_pos", "fixed_pos", "ev_pos", "hp_pos"]:
#         fig.add_trace(go.Scatter(x=np.arange(0,8760,1), y=consumer_timeseries[consumer][plot_item], mode='lines', name=plot_item + "_" + consumer))
# # print the max and sum consumption as the title of the plot
# fig.update_layout(title="sum consumption/generation for consumer " + consumer)
# fig.show()

# # plot time series of sum consumption of all consumers for a given asset using plotly--------------------------------------------------------------------------------------------
# fig = go.Figure()
# for plot_item in ["positive_consumption", "pv_pos", "fixed_pos", "ev_pos", "hp_pos"]:
#     sum_consumption = []
#     for i in range(8760):
#         sum_consumption.append(0)
#         for consumer in consumer_timeseries.keys():
#             sum_consumption[i] += consumer_timeseries[consumer][plot_item][i]
#     fig.add_trace(go.Scatter(x=np.arange(0,8760,1), y=sum_consumption, mode='lines', name=plot_item))
# # print the max and sum consumption as the title of the plot
# fig.update_layout(title="sum consumption/generation for all consumers")
# fig.show()
