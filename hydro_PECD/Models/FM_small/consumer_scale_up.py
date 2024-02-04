# from data_prep.definitions_common import *
from data_prep.definitions_common import (
    gen_max_EV_BT_data,
    pmp_max_EV_BT_data,
    gen_energy_max_EV_BT_data,
    Demand_data,
    Consumer_import_max,
    Consumer_export_max,
    imported_all_consumers,
    exported_all_consumers,
    Data_plant_flex_d_within_window,
    Infeed_consumers,
    Outflow_data,
    Map_plant_tech,
    Map_plant_node,
    Plant_list,
    Map_consumer_plant,
    Map_tech_plant,
    Map_node_plant,
    Avail_plant,
    Map_eff_in_plant,
    Map_eff_out_plant,
    Plant_list_rep_bat,
)

from data_prep.definitions_NETFLEX import (
    gen_max_EV_BT_data_netflex,
    pmp_max_EV_BT_data_netflex,
    gen_energy_max_EV_BT_data_netflex,
    Consumer_import_max_netflex,
    Consumer_export_max_netflex,
    Data_plant_flex_d_within_window_netflex,
    Infeed_consumer_netflex,
    Outflow_data_ev_netflex,
)


def remove_string_from_value(value, string_to_remove):
    """
    Function that gets a value (of a dictionary) and removes string_to_remove.
    It will be used to remove a given plant from a Mapping dictionary.
    """

    if isinstance(value, list):
        value[:] = [item for item in value if item != string_to_remove]
    elif isinstance(value, str):
        value = value.replace(string_to_remove, "")
    return value


def consumer_demand_scale(consumers_representing):
    """
    This function scales up the number of consumers in the model, by scaling up each consumer's net deamnd from their optimizations.
    """
    # Demand time series ---------------------------------------------------------
    # Replacing Demand_data with data from consumers' optimization.
    # Demand_data["ID299", t] is now the fixed demand of consumer 299.
    # Demand_data["ID299", t] will be the demand of consumer 299, if it is optimized in the consumer optimization.
    for consumer in imported_all_consumers:
        for consumer, t in imported_all_consumers[consumer]:
            Demand_data[consumer, "fixed", t] = (
                consumers_representing
                * imported_all_consumers[consumer][consumer, t].value
                - consumers_representing
                * exported_all_consumers[consumer][consumer, t].value
            )


def consumer_asset_demand_scale(
    consumers_representing, Consumer_list, T_list, single_large_battery=True
):
    """
    This function scales up the assets owned by consumers in the model, by consumers_representing times, both in sizes (power and energy) and consumption.
    If single_large_battery is True, it first creates one large battery summing up battery assets of all consumers. This will reduces computation effort required.
    """
    # A. Scaling up fixed demand of consumers ------------------------------------
    for consumer in Consumer_list:
        for t in T_list:
            Demand_data[consumer, "fixed", t] = (
                consumers_representing * Demand_data[consumer, "fixed", t]
            )

    # B. Scaling up assets of consumers ------------------------------------------

    # Multilply all values in gen_max_EV_BT_data_netflex pmp_max_EV_BT_data_netflex gen_energy_max_EV_BT_data_netflex with consumers_representing
    # Assuming gen_max_EV_BT_data, pmp_max_EV_BT_data, gen_energy_max_EV_BT_data, Consumer_import_max, Data_plant_flex_d_within_window, Infeed_consumers, and Outflow_data are already defined dictionaries.

    # If one single large battery is to replace batteries of all consumers in NETFLEX
    if single_large_battery:
        # To create one large representative batter:
        # Step 1:
        # create a list of all battery plants (list of plants in gen_max_EV_BT_data_netflex whose Map_plant_tech == "bt")
        bt_plants = [
            plant
            for plant in gen_max_EV_BT_data_netflex.keys()
            if Map_plant_tech[plant] == "bt"
        ]

        # Step 2:
        # Copy necesseray info
        # Information other than size (e.g., location) of the representative battery should be copied from the first battery plant.
        bt_to_copy_some_param_from = bt_plants[0]

        # location of the representatie battery
        node_location = Map_plant_node[bt_to_copy_some_param_from]

        # Naming the new battery
        new_name_bt_single_large = "bt_single_large"

        # Step 3:
        # Compute the sum of values associated with the original batteries
        gen_sum_bt = consumers_representing * sum(
            value
            for plant, value in gen_max_EV_BT_data_netflex.items()
            if plant in bt_plants
        )

        pmp_sum_bt = consumers_representing * sum(
            value
            for plant, value in pmp_max_EV_BT_data_netflex.items()
            if plant in bt_plants
        )

        eng_sum_bt = consumers_representing * sum(
            value
            for plant, value in gen_energy_max_EV_BT_data.items()
            if plant in bt_plants
        )

        # Step 4:
        # Updating values for EVs (anything but batteries) and removing values for batteries
        for plant in gen_max_EV_BT_data_netflex:
            if plant not in bt_plants:
                gen_max_EV_BT_data[plant] = (
                    consumers_representing * gen_max_EV_BT_data_netflex[plant]
                )

                pmp_max_EV_BT_data[plant] = (
                    consumers_representing * pmp_max_EV_BT_data_netflex[plant]
                )

                gen_energy_max_EV_BT_data[plant] = (
                    consumers_representing * gen_energy_max_EV_BT_data_netflex[plant]
                )

            # if the plant is a battery, remove it from dictionaries and lists.
            else:
                gen_max_EV_BT_data.pop(plant)
                pmp_max_EV_BT_data.pop(plant)
                gen_energy_max_EV_BT_data.pop(plant)
                Map_plant_tech.pop(plant)
                Map_plant_node.pop(plant)
                Plant_list.remove(plant)
                # remove "plant" from Map_consumer_plant. Important: this approach updates the dictionary, instead of redefining the dictionary.
                for key, value in Map_consumer_plant.items():
                    Map_consumer_plant[key] = remove_string_from_value(value, plant)
                # remove "plant" from Map_node_plant. Important: this approach updates the dictionary, instead of redefining the dictionary.
                for key, value in Map_node_plant.items():
                    Map_node_plant[key] = remove_string_from_value(value, plant)

        # Step 5:
        # Add the new "bt_single_large" plant to dictionaries and lists.
        # Adding new_name_bt_single_large to Plant_list_rep_bat makes its name available to fix capacities step in the core code.
        Plant_list_rep_bat.append(new_name_bt_single_large)
        gen_max_EV_BT_data[new_name_bt_single_large] = gen_sum_bt
        pmp_max_EV_BT_data[new_name_bt_single_large] = pmp_sum_bt
        gen_energy_max_EV_BT_data[new_name_bt_single_large] = eng_sum_bt
        Map_plant_tech.update({new_name_bt_single_large: "bt"})
        Map_plant_node.update({new_name_bt_single_large: node_location})
        Plant_list.append(new_name_bt_single_large)

        if "bt" in Map_tech_plant:
            Map_tech_plant["bt"].append(new_name_bt_single_large)
        else:
            Map_tech_plant.update({"bt": [new_name_bt_single_large]})

        Map_node_plant[node_location].append(new_name_bt_single_large)

        T_list_in_Avail_plant = [key[1] for key in Avail_plant]
        for t in T_list_in_Avail_plant:
            Avail_plant[new_name_bt_single_large, t] = Avail_plant[
                bt_to_copy_some_param_from, t
            ]
        Map_eff_in_plant[new_name_bt_single_large] = Map_eff_in_plant[
            bt_to_copy_some_param_from
        ]
        Map_eff_out_plant[new_name_bt_single_large] = Map_eff_out_plant[
            bt_to_copy_some_param_from
        ]

    # If else each battery remains its own single battery.
    else:
        # Updating gen_max_EV_BT_data based on gen_max_EV_BT_data_netflex
        for plant in gen_max_EV_BT_data_netflex:
            gen_max_EV_BT_data[plant] = (
                consumers_representing * gen_max_EV_BT_data_netflex[plant]
            )

        # Updating pmp_max_EV_BT_data based on pmp_max_EV_BT_data_netflex
        for plant in pmp_max_EV_BT_data_netflex:
            pmp_max_EV_BT_data[plant] = (
                consumers_representing * pmp_max_EV_BT_data_netflex[plant]
            )

        # Updating gen_energy_max_EV_BT_data based on gen_energy_max_EV_BT_data_netflex
        for plant in gen_energy_max_EV_BT_data_netflex:
            gen_energy_max_EV_BT_data[plant] = (
                consumers_representing * gen_energy_max_EV_BT_data_netflex[plant]
            )

    # Updating Consumer_import_max based on Consumer_import_max_netflex
    for consumer in Consumer_import_max_netflex:
        Consumer_import_max[consumer] = (
            consumers_representing * Consumer_import_max_netflex[consumer]
        )

    # Updating Consumer_export_max based on Consumer_import_max_netflex (assuming they have the same keys)
    for consumer in Consumer_import_max_netflex:
        Consumer_export_max[consumer] = (
            consumers_representing * Consumer_export_max_netflex[consumer]
        )

    # Updating Data_plant_flex_d_within_window based on Data_plant_flex_d_within_window_netflex
    for plant in Data_plant_flex_d_within_window_netflex:
        Data_plant_flex_d_within_window[plant]["energy"] = [
            consumers_representing
            * Data_plant_flex_d_within_window_netflex[plant]["energy"][i]
            for i in range(
                len(Data_plant_flex_d_within_window_netflex[plant]["energy"])
            )
        ]
        
        Data_plant_flex_d_within_window[plant]["max_demand"] = (
            consumers_representing
            * Data_plant_flex_d_within_window_netflex[plant]["max_demand"]
        )

    # Updating Infeed_consumers based on Infeed_consumer_netflex
    for consumer, tech, t in Infeed_consumer_netflex:
        Infeed_consumers[(consumer, tech, t)] = (
            consumers_representing * Infeed_consumer_netflex[(consumer, tech, t)]
        )

    # Updating Outflow_data based on Outflow_data_ev_netflex
    for plant, t in Outflow_data_ev_netflex:
        Outflow_data[(plant, t)] = (
            consumers_representing * Outflow_data_ev_netflex[(plant, t)]
        )
