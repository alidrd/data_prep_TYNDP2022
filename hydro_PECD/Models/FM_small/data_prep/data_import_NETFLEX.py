import time
import json
from read_settings import read_scenario_settings
from data_prep.definitions_common import (
    Consumer_list,
    Plant_list,
    Map_plant_tech,
    Map_plant_node,
    Infeed_consumers,
    Tech_list,
    Map_consumer_node,
    Avail_plant,
)
from data_prep.definitions_common import (
    Outflow_data,
    Plant_outflow_list,
    Map_consumer_plant,
    Map_consumer_node,
    Map_consumer_optimization,
    Consumer_import_max,
)
from data_prep.definitions_common import (
    Consumer_export_max,
    Demand_data,
    Data_plant_flex_d_within_window,
    Infeed_consumers,
    Map_eff_in_plant,
    Map_eff_out_plant,
    LineATC_list,
)
from data_prep.definitions_common import (
    gen_max_EV_BT_data,
    pmp_max_EV_BT_data,
    gen_energy_max_EV_BT_data,
    Map_node_plant,
    Map_node_consumer,
)
from data_prep.definitions_NETFLEX import *
from structural_parameters import (
    tech_demand_with_timeseries_netflex_list,
    tech_infeed_consumers_list,
)
from data_import_fcns import (
    ev_avail_discharge_calculator,
    tou_tariff,
)


def data_import_NETFLEX_fcn(scenario_name):
    """
    This function imports the data from the NETFLEX json files.
    Input:
        scenario_name: name of the scenario 
    Output:
        Updated values for several global variables both lists (shown by .extend()) and dictionaries (shown by .update()).
        Example: Map_plant_tech.update(Map_plant_tech_consumer_netflex)
    """
    settings_scen = read_scenario_settings(scenario_name)
    # weather_year = settings_scen['weather_year']
    # run_year = settings_scen['run_year']
    # eu_policy = settings_scen['eu_policy']
    # ch_policy = settings_scen['ch_policy']
    Consumer_list_netflex = settings_scen["Consumer_list_netflex"]
    T_list = settings_scen["T_list"]


    # basic parameters -------------------------------------------------------
    consumer_import_max_scaler = 0.020  # MW NOTE: maybe define in json file?
    consumer_export_max_scaler = 0.020  # MW NOTE: maybe define in json file?


    # ------------------------------------------------------------------------
    # read the data - from NETFLEX json files --------------------------------
    # ------------------------------------------------------------------------
    start_time = time.time()
    print("Reading NETFLEX data from json files ...")

    consumer_data = {}
    for consumer in Consumer_list_netflex:
        consumer_data[consumer] = json.load(
            open("input/consumers/" + consumer + ".json")
        )

    Consumer_list.extend(Consumer_list_netflex)
    print("consumer_data json imported in {} seconds".format(time.time() - start_time))


    # ------------------------------------------------------------------------
    # fill the parameters for the consumers ----------------------------------
    # ------------------------------------------------------------------------
    print("Filling the parameters for the consumers ...")
    for consumer in Consumer_list_netflex:
        # assing consumer_data[consumer]["assets"]["list"] to Map_consumer_plant_netflex[consumer] if the plant is not "fixed"
        Map_consumer_plant_netflex[consumer] = [
            plant
            for plant in consumer_data[consumer]["assets"]["list"]
            if plant.split("_")[0] != "fixed"
        ]
        Plant_list_netflex.extend(
            [
                plant
                for plant in consumer_data[consumer]["assets"]["list"]
                if plant.split("_")[0] != "fixed" and plant.split("_")[0] != "pv"
            ]
        )  # fixed is the fixed demand of the consumer, pv is infeed, should not be a plant (where later plants are generating actively)
        Map_consumer_node_netflex[consumer] = consumer_data[consumer]["node"]
        Map_consumer_optimization_netflex[consumer] = consumer_data[consumer][
            "optimization"
        ]
        Consumer_import_max_netflex[consumer] = consumer_import_max_scaler
        Consumer_export_max_netflex[consumer] = consumer_export_max_scaler
        # for all plants of a consumer
        for plant in consumer_data[consumer]["assets"]["list"]:
            # get the technology of the plant
            tech_plant = plant.split("_")[0]

            # if the plant is not "fixed", then it is a plant, and need to be added to the dictionaries
            if tech_plant != "fixed":
                if tech_plant == "v1g":
                    # NOTE: this is a simplification. EVs are considered as V1G for the time being.
                    Map_plant_tech_consumer_netflex[plant] = "v1g"

                elif tech_plant == "hp":
                    Map_plant_tech_consumer_netflex[plant] = "hp"

                else:
                    Map_plant_tech_consumer_netflex[plant] = tech_plant
                Map_plant_node_consumer_netflex[plant] = consumer_data[consumer]["node"]

            if tech_plant in tech_demand_with_timeseries_netflex_list:
                Demand_data_consumer_netflex.update(
                    {
                        (consumer, tech_plant, t): consumer_data[consumer]["assets"][
                            plant
                        ]["asset_time_series"][t]
                        for t in T_list
                    }
                )
            elif tech_plant in tech_infeed_consumers_list:
                Infeed_consumer_netflex.update(
                    {
                        (consumer, tech_plant, t): -consumer_data[consumer]["assets"][
                            plant
                        ]["asset_time_series"][t]
                        for t in T_list
                    }
                )

            # Flexibility characteristics of flexible demand
            # pv, fixed (fixed deamnd) and batteries have no flexibility characteristics
            if tech_plant != "pv" and tech_plant != "fixed" and tech_plant != "bt":
                # NOTE: might not work because time_horizon is in [] form, not () form
                Data_plant_flex_d_within_window_netflex[plant] = {
                    key: consumer_data[consumer]["assets"][plant][key]
                    for key in ["time_horizon", "energy", "max_demand"]
                }

            # availability and other characteristics of plants
            if tech_plant == "v1g":
                Map_eff_in_plant_netflex[plant] = (
                    consumer_data[consumer]["assets"][plant][
                        "charging_efficiency_roundtrip"
                    ]
                    ** 0.5
                )
                Map_eff_out_plant_netflex[plant] = (
                    consumer_data[consumer]["assets"][plant][
                        "charging_efficiency_roundtrip"
                    ]
                    ** 0.5
                )
                gen_max_EV_BT_data_netflex[plant] = consumer_data[consumer]["assets"][
                    plant
                ]["max_demand"]
                pmp_max_EV_BT_data_netflex[plant] = consumer_data[consumer]["assets"][
                    plant
                ]["max_demand"]
                gen_energy_max_EV_BT_data_netflex[plant] = consumer_data[consumer][
                    "assets"
                ][plant]["battery_size"]
                (
                    Avail_plant_consumer_netflex_single_plant,
                    Outflow_data_ev_netflex_single_plant,
                ) = ev_avail_discharge_calculator(
                    consumer_data[consumer]["assets"][plant]["asset_time_series"],
                    plant,
                    T_list,
                )

                Avail_plant_consumer_netflex.update(
                    Avail_plant_consumer_netflex_single_plant
                )

                Outflow_data_ev_netflex.update(Outflow_data_ev_netflex_single_plant)

                Plant_outflow_list_netflex.append(plant)

            elif tech_plant == "bt":
                # fully available for all time steps
                Avail_plant_consumer_netflex.update({(plant, t): 1 for t in T_list})

                Map_eff_in_plant_netflex[plant] = (
                    consumer_data[consumer]["assets"][plant][
                        "charging_efficiency_roundtrip"
                    ]
                    ** 0.5
                )
                Map_eff_out_plant_netflex[plant] = (
                    consumer_data[consumer]["assets"][plant][
                        "charging_efficiency_roundtrip"
                    ]
                    ** 0.5
                )
                gen_max_EV_BT_data_netflex[plant] = consumer_data[consumer]["assets"][
                    plant
                ]["max_demand"]
                pmp_max_EV_BT_data_netflex[plant] = consumer_data[consumer]["assets"][
                    plant
                ]["max_demand"]
                gen_energy_max_EV_BT_data_netflex[plant] = consumer_data[consumer][
                    "assets"
                ][plant]["battery_size"]

            # availability data is not needed for fixed (fixed demand).
            elif tech_plant != "fixed":
                # fully available for all time steps
                Avail_plant_consumer_netflex.update({(plant, t): 1 for t in T_list})


    # ------------------------------------------------------------------------
    # update main parameters with the consumer parameters --------------------
    # ------------------------------------------------------------------------
    print("Updating main parameters with the consumer parameters")

    Plant_list.extend(Plant_list_netflex)

    Map_plant_tech.update(Map_plant_tech_consumer_netflex)

    # add all consumer techs to tech list, minus "fixed"
    techs = list(set(Map_plant_tech_consumer_netflex.values()))
    Tech_list.extend(techs)

    Map_plant_node.update(Map_plant_node_consumer_netflex)

    Avail_plant.update(Avail_plant_consumer_netflex)

    Outflow_data.update(Outflow_data_ev_netflex)

    Plant_outflow_list.extend(Plant_outflow_list_netflex)

    Map_consumer_plant.update(Map_consumer_plant_netflex)

    Map_consumer_node.update(Map_consumer_node_netflex)

    Map_consumer_optimization.update(Map_consumer_optimization_netflex)

    Demand_data.update(Demand_data_consumer_netflex)

    Consumer_import_max.update(Consumer_import_max_netflex)

    Consumer_export_max.update(Consumer_export_max_netflex)

    Data_plant_flex_d_within_window.update(Data_plant_flex_d_within_window_netflex)

    Infeed_consumers.update(Infeed_consumer_netflex)

    Map_eff_in_plant.update(Map_eff_in_plant_netflex)

    Map_eff_out_plant.update(Map_eff_out_plant_netflex)

    gen_max_EV_BT_data.update(gen_max_EV_BT_data_netflex)

    pmp_max_EV_BT_data.update(pmp_max_EV_BT_data_netflex)

    gen_energy_max_EV_BT_data.update(gen_energy_max_EV_BT_data_netflex)

    # TODO: at this point, Node_list_netflex is not added to Node_list, because always CH00
    Node_list_netflex = list(set(Map_plant_node_consumer_netflex.values()))

    # ------------------------------------------------------------------------
    # update Mappings --------------------------------------------------------
    # ------------------------------------------------------------------------

    for node in Node_list_netflex:
        # Map_node_plant
        # Coding approach below updates Map_node_plant (extend), instead of overwriting it (assign).
        # setdefault() checks if the node key already exists in Map_node_plant. If it does, it returns the list associated with it. If it doesn't, it creates a new key with an empty list.
        Map_node_plant.setdefault(node, []).extend(
            p for p in Plant_list_netflex if Map_plant_node_consumer_netflex[p] == node
        )

        # Map_node_consumer
        Map_node_consumer.setdefault(node, []).extend(
            c for c in Consumer_list_netflex if Map_consumer_node_netflex[c] == node
        )

    # NETFLEX has no lines, so the list is empty, as defined in definitions.py
    LineATC_list.extend([])

    print("consumer data imported in {} seconds".format(time.time() - start_time))
