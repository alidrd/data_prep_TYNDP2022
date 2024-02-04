import pandas as pd
import csv
from mappings import (
    RES_tech_mapping_ERA5_ours,
    Map_planttech_SM_ours,
    Map_day_hour,
    Map_planttech_ours_SM,
)
from structural_parameters import tech_infeed_consumers_list
import re
import json


def read_hydro_capacities(Node_list, rep_hydro_plants):
    """
    Read the hydro capacities from the csv file input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_country_table.csv and save them in a dictionary.
    The values are fixed throughout the years and scenarios, so there are no year/scenario required as arguments to the function.
    Input:
        Node_list: list of nodes
        rep_hydro_plants: boolean, if True, the Swiss psp open hydro plants are represented by three representative generators, instead of one.    
    Output:
        Plant_list: list of plant names
        Map_plant_tech: dictionary with keys in the form of "region_RES_tech" (plant names) and values in the form of "tech" (technology names)
        Map_plant_node: dictionary with keys in the form of "region_RES_tech" (plant names) and values in the form of "node" (node names)
        hydro_capacities_MW: dictionary with keys in the form of "region_RES_tech" (plant names) and values in MW
        hydro_storage_MWh: dictionary with keys in the form of "region_RES_tech" (plant names) and values in MWh
        hydro_capacities_pumping_MW: dictionary with keys in the form of "region_RES_tech" (plant names) and values in MW

    """
    # read the csv file input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_country_table.csv and save it in a dataframe
    hydro_capacities_data = pd.read_csv(
        "input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_table.csv", header=0
    )
    # if hydro_capacities_data has any keys of RES_tech_mapping_ERA5_ours in the column "technology", replace them with the values of RES_tech_mapping_ERA5_ours
    hydro_capacities_data["technology"] = hydro_capacities_data["technology"].replace(
        RES_tech_mapping_ERA5_ours
    )

    #create a name column in hydro_capacities_data that is the sum of the columns "area" and "technology"
    hydro_capacities_data["name"] = hydro_capacities_data["area"]+ "_"+hydro_capacities_data["technology"]


    rep_hydro_plants_data = pd.DataFrame()
    if rep_hydro_plants:
        rep_hydro_plants_data = pd.read_csv(
            "input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_table_representative_plants.csv",
            header=0,
        )
        # if rep_hydro_plants_data has any keys of RES_tech_mapping_ERA5_ours in the column "technology", replace them with the values of RES_tech_mapping_ERA5_ours
        rep_hydro_plants_data["technology"] = rep_hydro_plants_data[
            "technology"
        ].replace(RES_tech_mapping_ERA5_ours)

        # from hydro_capacities_data, remove the rows that "CH00" is in the column "area" and "pumped_open" is in the column "technology"
        hydro_capacities_data = hydro_capacities_data[
            ~(
                (hydro_capacities_data["area"] == "CH00")
                & (hydro_capacities_data["technology"] == "psp_open")
            )
        ]

        # cancat rep_hydro_plants_data to hydro_capacities_data 
        hydro_capacities_data = pd.concat(
            [hydro_capacities_data, rep_hydro_plants_data]
        )

    plant_names_all_PECD = hydro_capacities_data.name.unique().tolist()

    # set column "value" and "name" as index
    hydro_capacities_data = hydro_capacities_data.set_index(["name", "variable"])    

    # print(hydro_capacities_data)
    # for regions in Node_list, for the row in hydro_capacities_data that has region in column 'area' and "gen_cap_MW" in column variable, read the value in column value and save it in a dictionary
    # if there is a KeyError, do not save the value in the dictionary
    Plant_list = []
    Map_plant_tech = {}
    Map_plant_node = {}
    hydro_capacities_MW = {}
    hydro_storage_MWh = {}
    hydro_capacities_pumping_MW = {}
    Map_consumer_plant = {}

    plants_in_target_region = [plant for plant in plant_names_all_PECD if hydro_capacities_data.loc[(plant, "gen_cap_MW")]["area"] in Node_list]

    for plant_name in plants_in_target_region:
        region = hydro_capacities_data.loc[(plant_name, "gen_cap_MW"), "area"]
        tech = hydro_capacities_data.loc[(plant_name, "gen_cap_MW"), "technology"]
        try:
            hydro_capacities_MW[plant_name] = hydro_capacities_data.loc[
                (plant_name, "gen_cap_MW")
            ]["value"].round(1) # type: ignore

            hydro_storage_MWh[plant_name] = round(
                1000 * hydro_capacities_data.loc[(plant_name, "sto_GWh"), "value"] # type: ignore
            )

            # add the plant to the list of plants
            Plant_list.append(plant_name)
            Map_plant_tech[plant_name] = tech
            Map_plant_node[plant_name] = region
            # if key [region + "_fixedconsumer"] exists in Map_consumer_plant, add to the key region + "_fixedconsumer" add the plant name, otherwise create the key and add the plant name
            if region + "_fixedconsumer" in Map_consumer_plant:
                Map_consumer_plant[region + "_fixedconsumer"].append(plant_name)
            else:
                Map_consumer_plant[region + "_fixedconsumer"] = [plant_name]

        except IndexError:
            print(
                f"IndexError for region {region} and tech {tech} for gen_cap_MW or sto_GWh"
            )
            pass

        if tech in ["psp_open", "psp_close"]:
            try:
                hydro_capacities_pumping_MW[plant_name] = - hydro_capacities_data.loc[
                    (plant_name, "pumping_cap_MW")]["value"].round(1) # type: ignore

            except IndexError:
                print(
                    f"IndexError for region {region} and tech {tech} for pumping_cap_MW"
                )
                pass

    return (
        Plant_list,
        Map_plant_tech,
        Map_plant_node,
        hydro_capacities_MW,
        hydro_storage_MWh,
        hydro_capacities_pumping_MW,
        Map_consumer_plant,
    )


def read_ror_Infeed_data(weather_year, Node_list):
    """
    Read the ROR Infeed data from the parquet file input/hydro_PECD/PECD_EERA2021_ROR_2030_gen.parquet and save them in a dictionary.
    The values are fixed throughout the scenarios, so there are no scenario required as arguments to the function.
    Output:
        ror_Infeed_data: dictionary with keys in the form of "region_ror" (plant names) and day_N with final values in MWh (e.g., ('CH00', 'day_305') 31796.0)
        for hourly generation, values should be divided by 24
    """

    hydro_inflow_data = pd.read_parquet(
        "input/hydro_PECD/PECD_EERA2021_ROR_2030_gen.parquet"
    )
    hydro_inflow_data["Day"] = hydro_inflow_data["Day"].astype(int)
    hydro_inflow_data["year"] = hydro_inflow_data["year"].astype(int)
    # hydro_inflow_data[(hydro_inflow_data.area_name=="CH00")&(hydro_inflow_data.year==1982)].sum()

    ror_Infeed_daily_data = {}
    ror_Infeed_hourly_data = {}
    Plant_list = []
    Map_plant_tech = {}
    Map_plant_node = {}

    for region in Node_list:
        # print(region)
        data_subset = hydro_inflow_data[
            (hydro_inflow_data["area_name"] == region)
            & (hydro_inflow_data["year"] == weather_year)
        ]
        grouped_data = data_subset.groupby("Day").first()["gen_GWh"]
        if (
            not grouped_data.isnull().all()
        ):  # if there is at least one value for the region
            plant_name = region + "_ror"
            Plant_list.append(plant_name)
            Map_plant_tech[plant_name] = "ror"
            Map_plant_node[plant_name] = region
            for day in range(1, 366):
                key = (region + "_fixedconsumer", "ror", "day_" + str(day))
                ror_Infeed_daily_data[key] = round(1000 * grouped_data.get(day, 0), 0)
    mapping_day_to_t = timemapping_creator("day", "t")
    for key in ror_Infeed_daily_data.keys():
        for new_time in mapping_day_to_t[key[2]]:
            # a68 used to be len(mapping_week_to_t[key[1]]), but this is not correct, because appearently the dataset reported values as if last week was a full week.
            ror_Infeed_hourly_data[(key[0], key[1], new_time)] = (
                ror_Infeed_daily_data[key] / 168
            )
    # export inflow_data_weekly_hourly with 7 digits after the comma
    return ror_Infeed_hourly_data, Plant_list, Map_plant_tech, Map_plant_node


def read_RES_avail_data(weather_year, Node_list):
    """
    Read renewable availability factors of a given technology data from csv file and store in dictionary Avail_plant_region.

    Arguments:
    weather_year -- integer, year of the weather data

    Returns:
    Avail_plant_RES_region -- dictionary, keys are the names of the regions (country/regions), values are lists of the renewable availability factors.
    e.g. ('NOS0_windof', 't_207'): 0.514291
    Avail_plant_RES_region[region_tech,t_N] -- float, renewable availability factor of RES plant of type "tech" region "region" in time step t

    """
    from mappings import RES_tech_mapping_ERA5_ours

    Avail_plant_RES_region = {}
    for RES_tech in ["LFSolarPV", "Offshore", "Onshore"]:
        with open(
            "input/RES_PECD/PECD_" + RES_tech + "_" + str(weather_year) + ".csv",
            newline="",
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                for region in Node_list:
                    plnat_name = region + "_" + RES_tech_mapping_ERA5_ours[RES_tech]
                    try:
                        Avail_plant_RES_region[plnat_name, row["t"]] = round(
                            float(row[region]), 7
                        )
                    except KeyError:
                        if row["t"] == "t_1":
                            print("KeyError for ", plnat_name, " in ", row["t"])
                    except ValueError:
                        if row["t"] == "t_1":
                            print("ValueError for ", plnat_name, " in ", row["t"])
    return Avail_plant_RES_region


def read_RES_capacities(scenario, year, Node_list):
    """
    Read RES capacity data from TYNDP-2020-Scenario-Datafile.xlsx and store in dictionary Res_capacity_dict.
    Input:
    scenario: string, scenario name (long name with space, e.g., "National Trends)
    year: integer, year of the weather data

    Output:
    Plant_list: list of plants. e.g. 'BE00_pvrf', 'BE00_windon', 'BE00_windof'
    Res_capacity_dict: dictionary with the values in the index as keys and the values in the column "Value" as values.
    e.g 'MK00_windon': 100.0
    """

    from mappings import Map_planttech_SM_ours

    Plant_list = []
    Map_plant_tech = {}
    Map_plant_node = {}
    Res_capacity_data = pd.read_excel(
        r"input/TYNDP-2020-Scenario-Datafile.xlsx",
        sheet_name="Capacity",
        header=0,
        index_col=False,
    )
    # find unique values in the column "Node/Line" and save them as a list
    # type: ignore
    Res_capacity_node_list = Res_capacity_data["Node/Line"].unique().tolist()
    # from Res_capacity_node_list, remove values that are not in Node_list
    Res_capacity_node_list = [x for x in Res_capacity_node_list if x in Node_list]
    # for every element in Res_capacity_node_list, read the value in in the column "Value" if in that row there is "Capacity" in the column "Parameter"
    Res_capacity_dict = {}
    for node in Res_capacity_node_list:
        for tech in ["Solar PV", "Onshore Wind", "Offshore Wind"]:
            # add node+ "_" + Map_planttech_SM_ours[tech] to list Plant_list
            plant_name = node + "_" + Map_planttech_SM_ours[tech]
            try:
                Res_capacity_dict[
                    node + "_" + Map_planttech_SM_ours[tech]
                ] = Res_capacity_data.loc[
                    (Res_capacity_data["Node/Line"] == node)
                    & (Res_capacity_data["Parameter"] == "Capacity")
                    & (Res_capacity_data["Scenario"] == scenario)
                    & (Res_capacity_data["Year"] == year)
                    & (Res_capacity_data["Climate Year"] == 1982)
                    & (Res_capacity_data["Generator_ID"] == tech),
                    "Value",
                ].values[
                    0
                ]
                Plant_list.append(plant_name)
                Map_plant_node[plant_name] = node
                Map_plant_tech[plant_name] = Map_planttech_SM_ours[tech]
            except IndexError:
                print("No data for " + plant_name)
    return Plant_list, Map_plant_tech, Res_capacity_dict, Map_plant_node


def cross_match_plant_list(Plant_capacity_gen_list, Plant_non_hydro_list):
    """ "
    This function checks if the plants in Plant_capacity_gen_list and Plant_non_hydro_list are the same.
    If not, it prints the plants that are in Plant_capacity_gen_list, but not in Plant_non_hydro_list and vice versa.
    """
    Plant_capacity_gen_common_list = list(
        set(Plant_capacity_gen_list) & set(Plant_non_hydro_list)
    )  # find values that are only in Plant_capacity_gen_list and Plant_non_hydro_list, not both
    # find values that are in Plant_capacity_gen_list, but not Plant_capacity_gen_common_list
    Plant_capacity_gen_diff_list = list(
        set(Plant_capacity_gen_list) - set(Plant_capacity_gen_common_list)
    )
    # find values that are in Plant_non_hydro_list, but not Plant_capacity_gen_common_list
    Plant_non_hydro_diff_list = list(
        set(Plant_non_hydro_list) - set(Plant_capacity_gen_common_list)
    )
    # if Plant_capacity_gen_diff_list is not empty, print the values in Plant_capacity_gen_diff_list
    if Plant_capacity_gen_diff_list != []:
        print(
            "The following plants are in capacities_....csv, but not in plants_....csv:"
        )
        print(Plant_capacity_gen_diff_list)
        # abort running the program and print the message in the brackets
        # Exception("Some plants cross-mismatch issue (1), see above")

    if (
        Plant_non_hydro_diff_list != []
    ):  # if Plant_non_hydro_diff_list is not empty, print the values in Plant_non_hydro_diff_list
        print(
            "The following plants are in plants_....csv, but not in capacities_...csv:"
        )
        # sort Plant_non_hydro_diff_list alphabetically
        print(Plant_non_hydro_diff_list)
        # Exception("Some plants cross-mismatch issue (2), see above")


def read_plant_non_hydro_data(allow_res_investment):
    """
    Read plant data from plants_non_hydro.csv file and store data in:
    Plant_non_hydro_list: list of plants
    Map_plant_node: dictionary with the values in the index as keys and the values in the column "node" as values
    Map_plant_tech: dictionary with the values in the index as keys and the values in the column "plant_type" as values
    """
    from mappings import Map_planttech_SM_ours

    Plant_non_hydro_data = pd.read_csv(
        r"input/plants_non_hydro.csv", header=0, index_col=0
    )

    # if the option allow_res_investment is activated, read the data from plants_res_CH.csv. Otherwise, create an empty dataframe and an empty list
    if allow_res_investment:
        Plant_res_ch_data = pd.read_csv(
            r"input/plants_res_CH.csv", header=0, index_col=0
        )  # NOTE: These are only including new investments on top of calculated infeed
        Plant_RES_CH_list = Plant_res_ch_data.index.tolist()
    else:
        Plant_res_ch_data = pd.DataFrame()
        Plant_RES_CH_list = []
    # Plant_hydro_EU = pd.read_csv(r'input/plants_hydro_EU.csv', header=0, index_col=0)  # NOTE: hydro data are being imported from PECD database for 2030 (no extra expansion was observed in TYNDP dataset anyways)
    # Plant_hydro_CH = pd.read_csv(r'input/plants_hydro_CH.csv', header=0, index_col=0)  # NOTE: hydro data are being imported from PECD database for 2030 (no extra expansion is currently modelled in CH)
    # Plant_all_data = pd.concat([Plant_non_hydro_data, Plant_hydro_EU, Plant_hydro_CH])
    Plant_all_data = pd.concat(
        [Plant_non_hydro_data, Plant_res_ch_data], ignore_index=False
    )  # + Plant_res_ch_data  Plant_non_hydro_data
    # if any of the keys of Map_planttech_SM_ours is mentioned as part of index of Plant_all_data, replace it with the value of Map_planttech_SM_ours
    Plant_all_data.index = Plant_all_data.index.str.replace(
        "|".join(Map_planttech_SM_ours.keys()),
        lambda x: Map_planttech_SM_ours[x.group()],
        regex=True,
    )
    Plant_all_data["tech"] = Plant_all_data["tech"].replace(Map_planttech_SM_ours)
    # save values in index as a list
    Plant_list = Plant_all_data.index.tolist()
    # save a dictionary with the values in the index as keys and the values in the column "node" as values
    Map_plant_node = Plant_all_data["market"].to_dict()
    # NOTE: if multiple nodes within CH, "node" should be used instead of "market", then several regions within CH should be connected
    # save a dictionary with the values in the index as keys and the values in the column "plant_type" as values
    Map_plant_tech = Plant_all_data["tech"].to_dict()
    Map_consumer_plant = {}
    # save a dictionary with the values in the index as keys and the values in the column "consumer" as values
    Map_plant_consumer = Plant_all_data["market"].to_dict()
    # for every unique value in values of Map_plant_consumer, find all keys that have that value and save them as the dictionary Map_consumer_plant
    for consumer in set(Map_plant_consumer.values()):
        Map_consumer_plant[consumer] = [
            k for k, v in Map_plant_consumer.items() if v == consumer
        ]

    return Plant_list, Plant_RES_CH_list, Map_plant_node, Map_plant_tech, Map_consumer_plant


def read_plant_non_hydro_capacities(scenario_EU, scenario_CH, year):
    """
    Read plant capacity data from nonhydro_capacities_gen.csv file and store data in:
    Plant_capacity_dict: dictionary with the values in the index as keys and the values in the column "year" and the given scenario as values
    """
    # import data
    Plant_capacity_nonhydro_data = pd.read_csv(
        r"input/nonhydro_capacities_gen.csv", header=0, index_col=0
    )
    Plant_capacity_nonhydro_data.index = Plant_capacity_nonhydro_data.index.str.replace(
        "|".join(Map_planttech_SM_ours.keys()),
        lambda x: Map_planttech_SM_ours[x.group()],
        regex=True,
    )

    # Plant_capacity_hydro_CH_data = pd.read_csv(r'input/capacities_gen_hydro_CH.csv', header=0, index_col=0)    #NOTE: Swissmod data is not used for hydro, but PECD data is used instead
    # Plant_capacity_pump_data     = pd.read_csv(r'input/capacities_pump.csv', header=0, index_col=0)              #NOTE: check if this is needed, now that we are importing directly
    # Plant_capacity_pump_CH_data  = pd.read_csv(r'input/capacities_pump_hydro_CH.csv', header=0, index_col=0)     #NOTE: Swissmod data is not used for hydro, but PECD data is used instead
    # merge EU plants and CH plants separately (scenario naming conventions are different
    # Plant_capacity_all_EU_data = pd.concat([Plant_capacity_data, Plant_capacity_pump_data])
    # Plant_capacity_all_CH_data = pd.concat([Plant_capacity_hydro_CH_data, Plant_capacity_pump_CH_data])
    # create a list of plants
    # Plant_capacity_all_EU_list = Plant_capacity_all_EU_data.index.tolist()
    # Plant_capacity_all_CH_list = Plant_capacity_all_CH_data.index.tolist()
    # Plant_capacity_gen_list = Plant_capacity_all_EU_list + Plant_capacity_all_CH_list
    # Plant_capacity_EU_dict = Plant_capacity_all_EU_data[str(year)][Plant_capacity_all_EU_data["scenario"] == scenario].to_dict()
    # Plant_capacity_CH_dict = Plant_capacity_all_EU_data[str(year)][Plant_capacity_all_EU_data["scenario"] == "all"].to_dict()
    # Plant_capacity = {**Plant_capacity_EU_dict, **Plant_capacity_CH_dict}

    # Plant_capacity_nonhydro_list = Plant_capacity_nonhydro_data.index.tolist()
    Plant_capacity_EU = Plant_capacity_nonhydro_data[str(year)][
        Plant_capacity_nonhydro_data["scenario"] == scenario_EU
    ].to_dict()
    Plant_capacity_CH = Plant_capacity_nonhydro_data[str(year)][
        Plant_capacity_nonhydro_data["scenario"] == scenario_CH
    ].to_dict()
    Plant_capacity_nonhydro_list = list(Plant_capacity_EU.keys()) + list(
        Plant_capacity_CH.keys()
    )

    return Plant_capacity_nonhydro_list, Plant_capacity_EU, Plant_capacity_CH


def read_demand_data(scenario, year, weather_year):
    """
    Read demand data from csv file and store in dictionary demand_data.

    Arguments:
    scenario -- string, name of the scenario
    year -- integer, year of the scenario
    weather_year -- integer, year of the weather data

    Returns:
    demand_data -- dictionary, keys are the names of the consumers with fixed demand (country/regions), values are lists of the demand in MW

    """
    Demand_data = {}
    with open(
        "input/demand/demand_"
        + scenario
        + "_"
        + str(year)
        + "_"
        + str(weather_year)
        + ".csv",
        newline="",
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        # in the variable reader, read the first row as the header and save values in consumer_list
        consumer_list = reader.fieldnames
        if consumer_list is not None:  # Check if consumer_list is not None
            for row in reader:
                for consumer in consumer_list[1:]:
                    # read values in row[consumer] with only 1 decimal
                    Demand_data[
                        consumer + "_fixedconsumer", "fixed", "t_" + row["t"]
                    ] = round(float(row[consumer]), 1)
        else:
            print("No demand data available for this scenario!")
    return Demand_data


def ev_avail_discharge_calculator(base_consumption_pattern, plant_name, T_list):
    """ "
    For a given time series of base consumption, calculate the availability of EVs and discharge patterns.
    EVs are unavailable in an hour if their consumption is positive in the next hour.
    Discharge pattern is just the base_consumption_pattern. #TODO: check if this is correct on NETFLEX assumptions

    Input:
        base_consumption_pattern: time series of base consumption in form of a dictionary with keys 't_1', 't_2', ..., 't_8760'
        plant_name: string, name of the plant
    Return:
        ev_avail: time series of availability of EVs, a dictionary with plant name and time steps as keys (as a tuple) and of 0s and 1s as values. eg. ('ev_ID67', 't_1'): 1
        discharge_pattern: time series of EV discharge, a dictionary with plant name and time steps as keys (as a tuple). eg. ('ev_ID67', 't_1'): 0.4
    """
    ev_avail = {}

    # hours in which EVs are forced to be available, to avoid infesibility
    T_available_forced_list = [T_list[0]] + [T_list[1]] + T_list[-24:]

    # EVs are unavailable only in the hour before consumption moves from 0 to something positive

    for t in T_list:
        t_plus_1 = "t_" + str(int(t.split("_")[1]) + 1)
        if t in T_available_forced_list:
            # Forcing EVs to be available in the first two hours and last 24 hours of the simulation
            ev_avail[plant_name, t] = 1
        elif base_consumption_pattern[t_plus_1] > 0:
            ev_avail[plant_name, t] = 0
        else:
            ev_avail[plant_name, t] = 1

    discharge_pattern = {}
    for t in T_list:
        # if t in T_available_forced_list:
        #     # Forcing EVs to be not consuming  in the first two hours and last 24 hours of the simulation
        #     discharge_pattern[plant_name, t] = 0
        # else:
        t_int = int(t.split("_")[1])
        discharge_pattern[plant_name, t] = base_consumption_pattern["t_" + str(t_int)]

    return ev_avail, discharge_pattern


def timemapping_creator(originP, targetP):
    """
    Create a dictionary with the mapping between the originP and targetP time periods.
    Input:
        originP: string with the name of the origin time period (e.g., "week")
        targetP: string with the name of the target time period (e.g., "t")
    Output:
        map_originP_targetP: dictionary with keys in the form of "originP_x" (e.g., "week_1") and values in the form of "targetP_y" (e.g., map_originP_targetP['week_38']: array(['t_6217', 't_6218', 't_6219'...])
    """

    map_originP_targetP = {}
    if originP != "t":
        timemap = pd.read_csv("input/timemaps_hydro_year.csv")
        unique_x = timemap[originP].unique()
        for x_val in unique_x:
            map_originP_targetP[x_val] = timemap[timemap[originP] == x_val][
                targetP
            ].values
    else:  # to make the code more efficient, if the originP is already "t", just read the timemap file and save it in the dictionary
        timemap = pd.read_csv("input/timemaps_hydro_year.csv", index_col=0, header=0)
        unique_x = timemap.index.to_list()
        for x_val in unique_x:
            map_originP_targetP[x_val] = timemap.loc[x_val, targetP]

    return map_originP_targetP


# read inflow data for dam and psp_open


def read_inflow_data_hourly(weather_year, Node_list, rep_hydro_plants):
    """
    Read the inflow data from the parquet file input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_inflow.parquet and save them in a dictionary.
    The values are fixed throughout the scenarios, so there are no scenario required as arguments to the function.
    input:
        weather_year: integer, year of the weather data
        Node_list: list of nodes
        rep_hydro_plants: if True, the inflow data is read for representative hydro plants, otherwise for all hydro plants
    Output:
        inflow_data_hourly: dictionary with keys in the form of "region_RES_tech" (plant names) and week_1 with final values in MWh (e.g., ('NOS0_pumped_open', 't_1'): 977722.0)
    """
    Plant_inflow_list_TYNDP = []
    hydro_inflow_data_weekly = pd.read_parquet(
        "input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_inflow.parquet"
    )
    hydro_inflow_data_weekly["Week"] = hydro_inflow_data_weekly["Week"].astype(int)
    hydro_inflow_data_weekly["year"] = hydro_inflow_data_weekly["year"].astype(int)

    inflow_data_weekly = {}
    for region in Node_list:
        for tech in ["reservoir", "pumped_open"]:
            data_subset = hydro_inflow_data_weekly[
                (hydro_inflow_data_weekly["area_name"] == region)
                & (hydro_inflow_data_weekly["technology"] == tech)
                & (hydro_inflow_data_weekly["year"] == weather_year)
            ]
            grouped_data = data_subset.groupby("Week").first()["inflow_GWh"]
            # renaming the technology to match the plant names in the model (reservior -> dam, pumped_open -> psp_open)
            # write a if statement to check if grouped_data is all nans
            if (
                not grouped_data.isnull().all()
            ): 
                plant_name = region + "_" + RES_tech_mapping_ERA5_ours[tech]

                # write a conditional statement that is True if rep_hydro_plants is True or if plant_name is not equal to "CH_psp_open"
                if (rep_hydro_plants == True) and (plant_name == "CH00_psp_open"):
                    rep_hydro_plants_data = pd.read_csv(
                        "input/hydro_PECD/PECD_EERA2021_reservoir_pumping_2030_table_representative_plants.csv",
                        header=0,
                    )                        

                    plant_names_list = rep_hydro_plants_data["name"].unique().tolist()
                    for plant_name in plant_names_list:
                        for N in range(1, 54):
                            key = (plant_name, "week_" + str(N))
                            # share is qual to value in the column "inflow_share" of the row where the column "name" is equal to plant_name
                            share = rep_hydro_plants_data.loc[
                                rep_hydro_plants_data["name"] == plant_name,
                                "inflow_share",
                            ].values[0]
                            inflow_data_weekly[key] = 1000 * round(grouped_data[N], 3) * share
                        Plant_inflow_list_TYNDP.append(plant_name)

                else:
                    for N in range(1, 54):
                        key = (plant_name, "week_" + str(N))
                        inflow_data_weekly[key] = 1000 * round(grouped_data[N], 3)
                    Plant_inflow_list_TYNDP.append(plant_name)
                
    inflow_data_hourly = {}
    mapping_week_to_t = timemapping_creator("week", "t")

    for key in inflow_data_weekly.keys():
        for new_time in mapping_week_to_t[key[1]]:
            # 168 used to be len(mapping_week_to_t[key[1]]), but this is not correct, because appearently the dataset reported values as if last week was a full week.
            inflow_data_hourly[(key[0], new_time)] = inflow_data_weekly[key] / 168
    # export inflow_data_weekly_hourly with 7 digits after the comma

    return inflow_data_hourly, Plant_inflow_list_TYNDP


def tou_tariff(Tariff_def, tariff_No, Consumer_list, T):
    """Returns the price of the tariff at time steps included in the list T.
    Input:
        Tarrif_def, in the tarrif named tarrif_No, there are keys "rates", has several sections (section_N) that includes hours in day (1 to 24) as a list of two elements and corresponding price in "price"
        Consumer_list: list of consumers to which the tariff_No applies
        T: list of time steps included in the tariff
    Output:
        tariff: dictionary with time steps as keys and corresponding price as values.
    """
    tariff = {}
    for consumer in Consumer_list:
        for t in T:
            t_int = int(t[2:])
            for section in Tariff_def[tariff_No]["rates"]:
                t_equivalent_1_24 = t_int % 24 + 1
                if (
                    t_equivalent_1_24
                    >= Tariff_def[tariff_No]["rates"][section]["h_in_day"][0]
                ) & (
                    t_equivalent_1_24
                    <= Tariff_def[tariff_No]["rates"][section]["h_in_day"][1]
                ):
                    tariff[consumer, t] = Tariff_def[tariff_No]["rates"][section][
                        "price"
                    ]
    return tariff


def map_tech_to_plant(Plant_list, Data_per_plant, Data_per_tech, Map_plant_tech):
    """
    This function maps technology data to plants, only if already not assigned, and only if the tech is mentioned in Data_per_tech.
    If the technology of a plant matches the technology in the Data_per_tech, Data_per_plant[plant] will be equal to corresponding value in Data_per_tech.
    Input:
        Plant_list: list of plants
        Data_per_tech: data per technology (e.g., start condition of plants per technology)
    Output:
        Data_per_plant: dictionary with mapped values to plants start condition per plant, e.g., {Map_eff_in_plant["battery_1"] = 0.8}
    """
    Data_per_plant = {}
    for plant in Plant_list:
        # if Plant_start_condition[plant] does not already have a value
        if plant not in Data_per_plant.keys():
            if Map_plant_tech[plant] in Data_per_tech.keys():
                Data_per_plant[plant] = Data_per_tech[Map_plant_tech[plant]]
    return Data_per_plant


def read_line_data(year, NTC_CH_ratio):
    """
    Reads the line data from the json file input/NTC/ATC_exportlimit_{year}.json and converts the keys from strings to tuples. json files were created by read_transfer_capacities(year) function.
    Input:
        year: year of the data (2025 or 2030)
    """
    import time

    start = time.time()
    with open(r"input/NTC/List_line_" + str(year) + ".json", "r") as file:
        List_line = json.load(file)

    with open(r"input/NTC/Map_line_node_" + str(year) + ".json", "r") as file:
        Map_line_node = json.load(file)

    df = pd.read_csv(r"input/NTC/ATC_exportlimit_" + str(year) + ".csv")
    # for the rows whose line_name column has "CH00", multiply the value in column "value" by NTC_CH_ratio
    df.loc[df["line_name"].str.contains("CH00"), "value"] = (
        df.loc[df["line_name"].str.contains("CH00"), "value"] * NTC_CH_ratio
    )
    ATC_exportlimit = dict(zip(zip(df["line_name"], df["t"]), df["value"]))

    df = pd.read_csv(r"input/NTC/ATC_importlimit_" + str(year) + ".csv")
    # for the rows whose line_name column has "CH00", multiply the value in column "value" by NTC_CH_ratio
    df.loc[df["line_name"].str.contains("CH00"), "value"] = (
        df.loc[df["line_name"].str.contains("CH00"), "value"] * NTC_CH_ratio
    )
    ATC_importlimit = dict(zip(zip(df["line_name"], df["t"]), df["value"]))

    return List_line, Map_line_node, ATC_exportlimit, ATC_importlimit


def calculate_infeed_TYNDP(
    Node_list, tech_infeed_all_list, gen_max_RES, Avail_plant_RES_year_scenario, T_list
):
    """
    Calculates the infeed of RES for each node, RES infeed technology and time step.
    Input:
        Node_list: list of nodes to calculate the infeed for
        tech_infeed_all_list: list of technologies that are considered as infeed RES
        gen_max_RES: dictionary with maximum generation of RES per technology and node, e.g., gen_max_RES["AT00_windon"] = 1000
        Avail_plant_RES_year_scenario: dictionary with available capacity of RES per technology and node, e.g., dictionary key: (AT00_windon, t_1): 0.5
        T_list: list of time steps. e.g., [t_1, t_2, t_3...]
    Output:
        Infeed_fcn: dictionary with infeed of RES per node, technology and time step, e.g., Infeed_fcn["AT00_fixedconsumer", "windon", t_1] = 500

    """
    Infeed_fcn = {}  # defined over c,tech,t
    # for all c in Node_list, for all tech in tech_list_data_import, for all t in T_list: Infeed_TYNDP[c,tech,t] = Avail_plant[c,tech,t] * gen_max_RES[c,tech] for c in Node_list for tech in tech_list_data_import for t in T_list
    for n in Node_list:
        for tech in tech_infeed_all_list:
            # if gen_max_RES[c +"_" + tech] exists, then gen_max = gen_max_RES[c +"_" + tech]
            if n + "_" + tech in gen_max_RES:
                gen_max = gen_max_RES[n + "_" + tech]
                for t in T_list:
                    Infeed_fcn[n + "_fixedconsumer", tech, t] = (
                        Avail_plant_RES_year_scenario[n + "_" + tech, t] * gen_max
                    )
    return Infeed_fcn


def import_avail_plant(
    Plant_list, Plant_RES_CH_list, T_list, Map_plant_node, Map_plant_tech, Map_node_country, Avail_plant_RES_year_scenario
):
    """
    Imports the availability of capacity [0,1] of plants per technology, node and time step.
    Input:
        Plant_list: list of plants
        T_list: list of time steps
        Map_plant_node: dictionary with mapping of plants to nodes, e.g., Map_plant_node["battery_1"] = "AT00"
        Map_plant_tech: dictionary with mapping of plants to technologies, e.g., Map_plant_tech["AT00_battery"] = "battery"
        Map_node_country: dictionary with mapping of nodes to countries, e.g., Map_node_country["AT00"] = "AT"
    Output:
        Avail_plant: dictionary with available capacity of plants per technology, node and time step, e.g., Avail_plant["AT00_battery", t_1] = 0.95
    """

    import csv

    Avail_plant = {}

    data_dict = {}
    default_data = {}

    # read default data
    with open(r"input/availability_factor_conventional.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        fieldnames = reader.fieldnames
        # ensure that fieldnames is not None before trying to access its elements.
        if fieldnames is not None:
            for row in reader:
                country = row["country"]
                tech = row["technology"]
                month_value = {}
                for month in fieldnames[2:]:
                    month_value[month] = float(row[month])

                if country == "Default":
                    default_data[tech] = month_value
        else:
            print("fieldnames is None!")

    # read data per country
    with open(r"input/availability_factor_conventional.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        fieldnames = reader.fieldnames
        # ensure that fieldnames is not None before trying to access its elements.
        if fieldnames is not None:
            for row in reader:
                country = row["country"]
                tech = row["technology"]
                data_dict[country] = {}
                month_value = {}
                if country != "Default":
                    for month in fieldnames[2:]:
                        month_value[month] = float(row[month])

                data_dict[country][tech] = month_value

    # if a country does not have a technology, use the default value
    for country in data_dict:
        for tech in default_data:
            if tech not in data_dict[country]:
                data_dict[country][tech] = default_data[tech]

    # if a country is values of Map_node_country, but not in data_dict, use the default value
    for node in Map_node_country:
        country = Map_node_country[node]
        if country not in data_dict:
            data_dict[country] = default_data

    map_t_month = timemapping_creator("t", "month")
    for plant in Plant_list:
        if plant in Plant_RES_CH_list:
           for t in T_list:
                Avail_plant[plant, t] = Avail_plant_RES_year_scenario[plant, t]
        else:
            node = Map_plant_node[plant]
            country = Map_node_country[node]
            tech = Map_plant_tech[plant]
            for t in T_list:
                Avail_plant[plant, t] = data_dict[country][tech][map_t_month[t]]

    return Avail_plant


def read_plant_energy_limited_data(
    eu_policy,
    ch_policy,
    Plant_list_TYNDP,
    Map_plant_tech,
    Map_plant_node,
    tech_limited_energy_list,
    weather_year,
    run_year,
):
    generation_annual = {}
    df_EU = pd.read_csv("input//generation.csv", sep=",", header=0)
    df_CH = pd.read_csv("input//generation_CH.csv", sep=",", header=0)

    for p in Plant_list_TYNDP:
        if Map_plant_tech[p] in tech_limited_energy_list:
            if Map_plant_node[p] != "CH00":
                generation_annual[p] = (
                    df_EU.loc[
                        (df_EU["scenario"] == eu_policy)
                        & (df_EU["zone"] == Map_plant_node[p])
                        & (df_EU["tech"] == Map_planttech_ours_SM[Map_plant_tech[p]])
                        & (df_EU["weather_year"] == weather_year),
                        str(run_year),
                    ].item()
                    * 1000
                )
                # generation values in EU are in GWh, we needed to convert them to MWh
            else:
                region_ch, tech_ch = p.split("_")
                generation_annual[p] = df_CH.loc[
                    (df_CH["scenario"] == ch_policy)
                    & (df_CH["region"] == region_ch)
                    & (df_CH["tech"] == Map_planttech_ours_SM[Map_plant_tech[p]])
                    & (df_CH["weather_year"] == "all"),
                    str(run_year),
                ].item()

    # for tech in tech_limited_energy_list:
    #     for node in Node_list:
    #         if not node.startswith("CH"):
    #             plant_name = node + "_" + tech
    #             generation_annual[plant_name] = df_EU.loc[(df_EU["scenario"] == eu_policy) & (df_EU["zone"] == node) & (
    #                 df_EU["tech"] == Map_planttech_ours_SM[tech]) & (df_EU["weather_year"] == weather_year), str(run_year)].item()
    #         else:
    #             if node == "CH00":
    #                 plant_name = node + "_" + tech
    #                 generation_annual[plant_name] = df_CH.loc[(df_CH["scenario"] == ch_policy) & (
    #                     df_CH["tech"] == Map_planttech_ours_SM[tech]) & (df_CH["weather_year"] == "all"), str(run_year)].sum()
    #             else:
    #                 raise ValueError("CH01-CH07 not implemented yet for biomass and energy_limited plants!")

    return generation_annual
