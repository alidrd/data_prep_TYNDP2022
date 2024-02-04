from input.cost_operation_invest_data import cost_component
import numpy as np
from mappings import Map_node_country


def get_cost_component(tech, year, cost_type):
    """
    Returns a certain cost component for a given technology and year
    tech: technology  (should be plant, but later mapped with Mapplanttech)
    year: year
    cost_type: can be "investment", "fixed_op", "fixed", "variable"
    """
    investment_cost = cost_component["investment_cost_chfMW"].get(tech, {}).get(year)
    fixed_op_cost = cost_component["fixed_op_cost_chfMW"].get(tech, {}).get(year)
    om_cost = cost_component["om_cost_eurMWH"].get(tech, {})
    var_cost = cost_component["om_cost_eurMWH"].get(tech, {}) + (
        cost_component["input_cost_scenario_ZERO"].get("co2", {}).get(year, {})
        * cost_component["emission_factor"].get(tech, {})
        / cost_component["efficiency"].get(tech, {})
    )

    if cost_type == "investment":
        return investment_cost
    elif cost_type == "fixed_op":
        return fixed_op_cost
    elif cost_type == "om":
        return om_cost
    elif cost_type == "var":
        return var_cost
    else:
        return np.nan


def create_tech_cost_dict(tech_list, cost_type, year):
    tech_cost = {}
    for tech in tech_list:
        cost = get_cost_component(tech, year, cost_type)
        tech_cost[tech] = cost
    return tech_cost


def read_op_cost_calibration():
    """Reads the op_cost_calibration.csv file and returns a dictionary op_cost_n_tech_calibration[node, tech] with the calibration values"""
    op_cost_country_tech_calibration = {}
    op_cost_n_tech_calibration = {}

    # read the file as a dictionary op_cost_country_tech_calibration[country, tech] = calibration value
    with open("input/op_cost_calibration.csv", "r") as f:
        lines = f.readlines()
        header = lines[0].strip().split(",")
        for line in lines[1:]:
            line = line.strip().split(",")
            country = line[0]
            for i, tech in enumerate(header[1:]):
                op_cost_country_tech_calibration[(country, tech)] = float(line[i + 1])

    # map op_cost_country_tech_calibration from countries to nodes in dictionary tech_list_in_calibration
    tech_list_in_calibration = list(
        set([key[1] for key in dict.keys(op_cost_country_tech_calibration)])
    )

    for node in Map_node_country:
        for tech in tech_list_in_calibration:
            op_cost_n_tech_calibration[(node, tech)] = op_cost_country_tech_calibration[
                (Map_node_country[node], tech)
            ]

    return op_cost_n_tech_calibration


Map_plant_tech_cost_component = {  # cap_op (only generation capacity and operation costs) or cap_op_energy (additional energy capacity)
    "pv": "cap_op",
    "pvrf": "cap_op",
    "windon": "cap_op",
    "windof": "cap_op",
    "gas": "cap_op",
    "biomass": "cap_op",
    "battery": "cap_op_energy",
    # at this point, bt is for household consumers and battery utility scale
    "bt": "cap_op_energy",
    "dam": "cap_op_energy",
    "psp_open": "cap_op_energy",
    "psp_close": "cap_op_energy",
    # for EVs, it should not matter, because gen and energy capacities are fixed later (not optimized)
    "v1g": "cap_op_energy",
    # for EVs, it should not matter, because gen and energy capacities are fixed later (not optimized)
    "v2g": "cap_op_energy",
    # for flexible demands (e.g. heat pumps), it should not matter, because gen and energy capacities are fixed later (not optimized)
    "hp": "cap_op_energy",
    "chp": "cap_op",
    "oil": "cap_op",
    "dsr": "cap_op",
    "hardcoal": "cap_op",
    "nuclear": "cap_op",
    "lignite": "cap_op",
}
tech_list = list(dict.keys(Map_plant_tech_cost_component))

# if a technology needs to track state of the storage
tech_store_list = [
    "battery",
    "bt",
    "hydrogen",
    "psp_open",
    "psp_close",
    "v1g",
    "v2g",
    "dam",
]
# if a technology has pumping capability, i.e., if energy can be added/consumed (v1g is included)
tech_store_pump_list = [
    "battery",
    "bt",
    "hydrogen",
    "psp_open",
    "psp_close",
    "v1g",
    "v2g",
    "hp",
]
# if one wants to force pump capacity= gen capacity (mostly simplifying investment decisions)
tech_store_equal_pump_max_gen_max_list = ["battery", "bt", "v2g"]
# if a technology has no generation capability (e.g. EVs)]
tech_p_no_gen = ["hp", "v1g"]
# if a technology has an infeed for utility scale plants (e.g. pvrf)
tech_infeed_all_list = ["pvrf", "windon", "windof", "ror", "pv"]
# if a technology has an infeed only for consumers  (e.g. pv)
tech_infeed_consumers_list = [
    "pv",
]
# # if a technology has an infeed only for core run (e.g. pvrf)
# tech_infeed_core_run_list = ["pvrf", "windon", "windof", "ror"]


# if a technology is a hydro plant
tech_hydro_list = ["dam", "psp_open", "psp_close"]

# if a store technology has inflow or outflow
tech_inflow_list = ["dam", "psp_open"]
# if a store technology has inflow or outflow
tech_outflow_list = ["psp_open", "v1g", "v2g"]
tech_limited_energy_list = ["biomass", "chp"]

# list of asset technolgies owned by the consuemrs in NETFLEX that are to be imported to  demand time series.
# Note that batteries are not included here, because they have no consumption time series.
tech_demand_with_timeseries_netflex_list = ["fixed", "hp", "v1g"]

# allowing v2g to exist, for later expansions
tech_demand_with_timeseries_netflex_model_list = ["fixed", "hp", "v1g", "v2g"]

# all consuming technologies that are owned by the consumers in NETFLEX.
tech_demand_assets_netflex_list = ["fixed", "hp", "bt", "v1g", "v2g"]

tech_demand_assets_shiftable_netflex_list = ["hp", "v1g", "v2g"]


# consuming technologies that remain as inflexible demand (e.g. fixed fixed household demand) in the setting case of flex_dem_active_for_consumer = True
tech_demand_inflex_in_flex_dem_active_for_consumer = [
    "fixed",
]

# tariff data -------------------------------------------------------------------------------------
tariff_export_definitions = {
    "tariff_1": {
        "type": "TOU",
        "rates": {
            "section_1": {
                "h_in_day": [1, 7],
                "price": 0.10,
            },
            "section_2": {
                "h_in_day": [8, 20],
                "price": 0.15,
            },
            "section_3": {
                "h_in_day": [21, 24],
                "price": 0.10,
            },
        },
    }, 

    "tariff_AEW": {
        "type": "TOU",
        "rates": {
            "section_1": {
                "h_in_day": [1, 7],
                "price": 0.0323,
            },
            "section_2": {
                "h_in_day": [8, 20],
                "price": 0.0323,
            },
            "section_3": {
                "h_in_day": [21, 24],
                "price": 0.0323,
            },
        },
    } #NOTE: these values appear highly suspicious, but are taken from the AEW website; https://www.aew.ch/sites/default/files/2022-08/AEW_Ruecklieferung_Herkunftsnachweis_2023.pdf
}

tariff_import_definitions = {
    "tariff_1": {
        "type": "TOU",
        "rates": {
            "section_1": {
                "h_in_day": [1, 7],
                "price": 0.20,
            },
            "section_2": {
                "h_in_day": [8, 20],
                "price": 0.30,
            },
            "section_3": {
                "h_in_day": [21, 24],
                "price": 0.20,
            },
        },
    }, 

    "tariff_AEW": {
        "type": "TOU",
        "rates": {
            "section_1": {
                "h_in_day": [1, 7],
                "price": 0.2117,
            },
            "section_2": {
                "h_in_day": [8, 19],
                "price": 0.264,
            },
            "section_3": {
                "h_in_day": [20, 24],
                "price": 0.2117,
            },
        },
    } # source: "Classic" tariff from https://www.aew.ch/sites/default/files/2022-08/AEW_Classic_2023.pdf
    
}




# for every technology -------------------------------------------------------
# costs - investment in capacity #NOTE: remove the plant types that have no investment (eg EVs), then adjust model.investment_genmax_slp  so that it is defined on a different set
# cost_data_inv_gen_int = {"pv": 0,     "gas": 0,  "limited_energy": 100000000 , "battery": 0,  "bt": 0,  "dam":0 , "psp_open": 0, "psp_close": 0, "v1g": 0, "v2g": 0, "hp": 0, "chp": 10000, "oil":1000, "dsr": 10000, "hardcoal":10000, "nuclear": 100000, "lignite": 100000}
# cost_data_inv_gen_slp = {"pv": 15,    "gas": 10, "limited_energy": 100000000, "battery": 10, "bt": 0,  "dam":10, "psp_open":10, "psp_close":10, "v1g": 0, "v2g": 0, "hp": 0, "chp": 10000, "oil":1000, "dsr": 10000, "hardcoal":10000, "nuclear": 100000, "lignite": 100000}
# NOTE: update, if intercept of investment cost is not zero
cost_data_inv_gen_int = {tech: 0 for tech in dict.keys(Map_plant_tech_cost_component)}
cost_data_inv_gen_slp = create_tech_cost_dict(
    list(dict.keys(Map_plant_tech_cost_component)), "investment", 2040
)  # TODO: change 2040 to run year

# costs - investment in energy capacity
cost_data_inv_e_int = {
    "biomass": 1000,
    "battery": 1000,
    "bt": 0,
    "dam": 0,
    "psp_open": 0,
    "psp_close": 0,
    "v1g": 0,
    "v2g": 0,
    "hp": 0,
}  # TODO: update limited_energy and battery
cost_data_inv_e_slp = {
    "biomass": 1000,
    "battery": 1000,
    "bt": 0,
    "dam": 0,
    "psp_open": 0,
    "psp_close": 0,
    "v1g": 0,
    "v2g": 0,
    "hp": 0,
}  # TODO: update biomass and battery


# costs - operation
# cost_data_opr_int = {"pv": 0,    "gas": 0, "limited_energy": 10, "battery": 0,  "bt": 0, "dam":0, "psp_open": 0, "psp_close": 0, "v1g": 0, "v2g": 0, "hp": 0, "chp": 10, "oil":100, "dsr": 1, "hardcoal":50, "nuclear": 1, "lignite": 70}
# cost_data_opr_slp = {"pv": 0,    "gas": 5, "limited_energy": 10, "battery": 0,  "bt": 0, "dam":0, "psp_open": 0, "psp_close": 0, "v1g": 0, "v2g": 0, "hp": 0, "chp": 10, "oil":100, "dsr": 1, "hardcoal":50, "nuclear": 1, "lignite": 70}

cost_data_opr_int = {tech: 0 for tech in dict.keys(Map_plant_tech_cost_component)}
cost_data_opr_slp = create_tech_cost_dict(
    list(dict.keys(Map_plant_tech_cost_component)), "var", 2040
)  # TODO: change 2040 to run year


# calibration of operational costs for every node and technology
# op_cost_n_tech_calibration[node, tech] = calibration value (values taken from SA calibration process)
op_cost_n_tech_calibration = read_op_cost_calibration()

# calibration of operational costs for every technology
# cost_data_opr_qdr[tech] is the quadratic term of the operational cost (values taken from SA calibration process)
cost_data_opr_qdr = {
    "pv": 0,  # 2 * 0
    "pvrf": 0,  # 2 * 0
    "gas": 2 * 0.002,  # 2 * 0.002
    "biomass": 0,  # 2 * 0.00004
    "chp": 0,  # 2 * 0.00004
    "battery": 0,  # 2 * 0
    "bt": 0,  # 2 * 0
    "dam": 0,  # 2 * 0
    "psp_open": 0,  # 2 * 0
    "psp_close": 0,  # 2 * 0
    "v1g": 0,  # 2 * 0
    "v2g": 0,  # 2 * 0
    "hp": 0,  # 2 * 0
    "chp": 0,  # 2 * 0
    "oil": 2 * 0.04,  # 2 * 0.04
    "dsr": 0,  # 2 * 0
    "hardcoal": 2 * 0.002,  # 2 * 0.002
    "nuclear": 0,  # 2 * 0.00004
    "lignite": 0,  # 2 * 0.00004
    "windon": 0,  # 2 * 0
    "windof": 0,  # 2 * 0
}
# defining the start condtion of storage technologies (to be assigned to all plants of this type of technology, not alreay having a value)
Start_condition_tech = {
    "v1g": 0.8,
    "v2g": 0.8,
    "dam": 0.95,
    "psp_open": 0.95,
    "psp_close": 0.95,
    "battery": 0.95,
    "bt": 0.95,
}

# # defining the end condtion of storage technologies (to be assigned to all plants of this type of technology, not alreay having a value)
# End_condition_tech = {
#     "v1g": 0.8,
#     "v2g": 0.8,
#     "dam": 0.95,
#     "psp_open": 0.95,
#     "psp_close": 0.95,
#     "battery": 0.95,
#     "bt": 0.95,
# }


# for every storage plant ----------------------------------------------------
Map_eff_in_tech = {
    "v1g": 1,  # TODO:adjust later
    "v2g": 0.90,
    "dam": 1,  # TODO: maybe remove this
    "psp_open": 0.87,
    "psp_close": 0.87,
    "battery": 0.90,
    # TODO: Important to make sure for the central runs, the correct value is used (for consumers that have "bt", the efficiency may be different from this)
    "bt": 0.90,
}

Map_eff_out_tech = {
    "v1g": 1,  # TODO:adjust later
    "v2g": 0.90,
    "dam": 1,  # TODO: maybe remove this
    "psp_open": 0.87,
    "psp_close": 0.87,
    "battery": 0.90,
    # TODO: Important to make sure for the central runs, the correct value is used (for consumers that have "bt", the efficiency may be different from this)
    "bt": 0.90,
}

# cost of lost load [$/MWh], will be used as default value for all consumers that have no lost load cost defined
lostlost_cost = 1000
