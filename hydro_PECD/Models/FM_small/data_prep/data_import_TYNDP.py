from data_prep.definitions_TYNDP import *
from data_prep.definitions_common import (
    Consumer_list,
    Map_consumer_node,
    Infeed_consumers,
    Plant_list,
    Map_consumer_plant,
    Map_plant_tech,
    Map_plant_node,
    Plant_capacity_gen,
    Plant_capacity_pmp,
    Plant_capacity_strg,
)
from data_prep.definitions_common import (
    scenario_name,
    Inflow_data,
    Plant_inflow_list,
    LineATC_list,
    Map_line_node,
    ATC_exportlimit,
    ATC_importlimit,
    Demand_data,
    Map_node_plant,
    Map_node_consumer,
    Map_node_exportinglineATC,
    Map_node_importinglineATC,
    Avail_plant,
    Demand_data_TYNDP,
    Infeed_RES_TYNDP,
    Data_plant_energy_limited,
)
from mappings import (
    Map_TYNDPscenario_short_longspaced,
    Map_TYNDPscenario_short_long,
    Map_node_country,
    Map_Prognosscenario_short_long,
)
from structural_parameters import (
    tech_infeed_all_list,
    tech_limited_energy_list,
)
from data_import_fcns import *
from read_settings import read_scenario_settings


def data_import_TYNDP_fcn(scenario_name):
    """
    This function imports the data from TYNDP files.
    Input:
        scenario_name: name of the scenario 
    Output:
        Updated values for several global variables both lists (shown by .extend()) and dictionaries (shown by .update()).
        Example: Map_plant_tech.update(Map_plant_tech_nonhydro)
    """
    settings_scen = read_scenario_settings(scenario_name)
    Node_list = settings_scen["Node_list"]
    weather_year = settings_scen["weather_year"]
    run_year = settings_scen["run_year"]
    eu_policy = settings_scen["eu_policy"]
    ch_policy = settings_scen["ch_policy"]
    T_list = settings_scen["T_list"]
    rep_hydro_plants = settings_scen["rep_hydro_plants"]
    allow_res_investment = settings_scen["res_investment_allowed"]
    NTC_CH_ratio = settings_scen["NTC_CH_ratio"]


    Consumer_list_TYNDP.extend([node + "_fixedconsumer" for node in Node_list])
    Consumer_list.extend(Consumer_list_TYNDP)

    Map_consumer_node_TYNDP = {
        node + "_fixedconsumer": node for node in Node_list}
    Map_consumer_node.update(Map_consumer_node_TYNDP)

    # RES availability data
    print("Reading RES availability and capacity data and calculate infeed...")
    Avail_plant_RES_year_scenario = read_RES_avail_data(
        weather_year, Node_list)
    # Avail_plant.update(Avail_plant_RES_year_scenario)

    # RES capacities
    (
        Plant_list_RES,
        Map_plant_tech_res,
        gen_max_RES,
        Map_plant_node_RES,
    ) = read_RES_capacities(
        Map_TYNDPscenario_short_longspaced[eu_policy], run_year, Node_list
    )
    # Plant_list_TYNDP.extend(Plant_list_RES)             # when they are treated as infeed, they are not included in the plant list
    # Map_plant_tech.update(Map_plant_tech_res)     # when they are treated as infeed, they are not included in the plant list
    # Map_plant_node.update(Map_plant_node_RES)     # when they are treated as infeed, they are not included in the plant list

    Infeed_RES_TYNDP_instance = calculate_infeed_TYNDP(
        Node_list, tech_infeed_all_list, gen_max_RES, Avail_plant_RES_year_scenario, T_list
    )
    # print all values in Infeed_TYNDP if the first key is "CH00"
    # for key, value in Infeed_TYNDP.items():
    #     if key[0] == "CH00":
    #         print(key, value)
    Infeed_consumers.update(Infeed_RES_TYNDP_instance)
    Infeed_RES_TYNDP.update(Infeed_RES_TYNDP_instance)

    # infeed data - ror
    (
        Infeed_ROR_TYNDP,
        Plant_list_ror,
        Map_plant_tech_ror,
        Map_plant_node_ror,
    ) = read_ror_Infeed_data(weather_year, Node_list)
    Infeed_consumers.update(Infeed_ROR_TYNDP)
    # Plant_list_TYNDP.extend(Plant_list_ror)
    # Map_plant_tech.update(Map_plant_tech_ror)
    # Map_plant_node.update(Map_plant_node_ror)

    # # hydro plant data
    print("Reading hydro plant data...")
    (
        Plant_list_rsrvr,
        Map_plant_tech_rsrvr,
        Map_plant_node_rsrvr,
        gen_max_MW_rsrvr,
        hydro_storage_MWh_rsrvr,
        hydro_capacities_pumping_MW_rsrvr,
        Map_consumer_plant_rsrvr,
    ) = read_hydro_capacities(Node_list, rep_hydro_plants)
    Plant_list_TYNDP.extend(Plant_list_rsrvr)
    Map_consumer_plant.update(Map_consumer_plant_rsrvr)
    Map_plant_tech.update(Map_plant_tech_rsrvr)
    Map_plant_node.update(Map_plant_node_rsrvr)
    Plant_capacity_gen.update(gen_max_MW_rsrvr)
    Plant_capacity_pmp.update(hydro_capacities_pumping_MW_rsrvr)
    Plant_capacity_strg.update(hydro_storage_MWh_rsrvr)

    # inflow data
    Inflow_data_pecd, Plant_inflow_list_TYNDP = read_inflow_data_hourly(
        weather_year, Node_list, rep_hydro_plants
    )
    Inflow_data.update(Inflow_data_pecd)
    Plant_inflow_list.extend(Plant_inflow_list_TYNDP)

    # non-hydro plant capacities
    print("Reading non-hydro plant capacities...")
    (
        Plant_list_nonhydro_capacity_gen,
        Plant_capacity_nonhydro_EU,
        Plant_capacity_nonhydro_CH,
    ) = read_plant_non_hydro_capacities(
        Map_TYNDPscenario_short_long[eu_policy], ch_policy, run_year
    )
    # Plant_list_TYNDP.extend(Plant_list_nonhydro_capacity_gen)
    Plant_capacity_gen.update(Plant_capacity_nonhydro_EU)
    Plant_capacity_gen.update(Plant_capacity_nonhydro_CH)

    # non-hydro plant other data
    (
        Plant_list_nonhydro,
        Plant_RES_CH_list,
        Map_plant_node_nonhydro,
        Map_plant_tech_nonhydro,
        Map_consumer_plant_nonhydro,
    ) = read_plant_non_hydro_data(allow_res_investment)
    techs_to_be_excluded = [
        "dsr",
    ]
    for plant in Plant_list_nonhydro:
        # if a plant constains strings in techs_to_be_excluded, remove the plant from the list
        if any(tech in plant for tech in techs_to_be_excluded):
            Plant_list_nonhydro.remove(plant)

    Plant_list_TYNDP.extend(Plant_list_nonhydro)
    Map_plant_node.update(Map_plant_node_nonhydro)
    Map_plant_tech.update(Map_plant_tech_nonhydro)
    Map_consumer_plant.update(Map_consumer_plant_nonhydro)

    # check if there is any cross-mismatch issue
    cross_match_plant_list(
        Plant_list_nonhydro_capacity_gen, Plant_list_nonhydro)
    Plant_list.extend(Plant_list_TYNDP)
    # Plant_list.extend(["pvrf_CH00", "windon_CH00"])

    print("Reading availabilities...")
    # calculate avail plant for non-hydro plants
    Avail_plant_TYNDP = import_avail_plant(
        Plant_list_TYNDP, Plant_RES_CH_list, T_list, Map_plant_node, Map_plant_tech, Map_node_country, Avail_plant_RES_year_scenario
    )
    Avail_plant.update(Avail_plant_TYNDP)

    # transmission lines data
    print("Reading transmission lines data...")
    (
        Line_list_TYNDP,
        Map_line_node_TYNDP,
        ATC_exportlimit_TYNDP,
        ATC_importlimit_TYNDP,
    ) = read_line_data(2030, NTC_CH_ratio)

    LineATC_list.extend(Line_list_TYNDP)
    Map_line_node.update(Map_line_node_TYNDP)
    ATC_exportlimit.update(ATC_exportlimit_TYNDP)
    ATC_importlimit.update(ATC_importlimit_TYNDP)

    # demand data
    print("Reading demand data...")
    Demand_data_year_scenario = read_demand_data(
        Map_TYNDPscenario_short_long[eu_policy], run_year, weather_year
    )
    Demand_data.update(Demand_data_year_scenario)
    Demand_data_TYNDP.update(Demand_data_year_scenario)

    # update Mappings
    for node in Node_list:
        # Map_node_plant
        # Coding approach below updates Map_node_plant (extend), instead of overwriting it (assign).
        # setdefault() checks if the node key already exists in Map_node_plant. If it does, it returns the list associated with it. If it doesn't, it creates a new key with an empty list.
        Map_node_plant.setdefault(node, []).extend(
            p
            for p in Plant_list_rsrvr + Plant_list_nonhydro
            if Map_plant_node[p] == node
        )

        # Map_node_consumer
        Map_node_consumer.setdefault(node, []).extend(
            c for c in Consumer_list_TYNDP if Map_consumer_node_TYNDP[c] == node
        )

        # Map_node_exportinglineATC
        Map_node_exportinglineATC.setdefault(node, []).extend(
            l for l in Line_list_TYNDP if node == Map_line_node_TYNDP[l]["start_node"]
        )

        # Map_node_importinglineATC
        Map_node_importinglineATC.setdefault(node, []).extend(
            l for l in Line_list_TYNDP if node == Map_line_node_TYNDP[l]["end_node"]
        )

    Data_plant_energy_limited_TYNDP = {}
    Data_plant_energy_limited_TYNDP = read_plant_energy_limited_data(
        Map_TYNDPscenario_short_long[eu_policy],
        Map_Prognosscenario_short_long[ch_policy],
        Plant_list_TYNDP,
        Map_plant_tech,
        Map_plant_node,
        tech_limited_energy_list,
        weather_year,
        run_year,
    )
    Data_plant_energy_limited.update(Data_plant_energy_limited_TYNDP)
