# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------ define lists and dictionaries etc. ------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# list of time steps (e.g. [t_6553, t_6554, ..., t_8760, t_1, t_2, ..., t_6552])
T_list = []

# list of nodes to be included in the model (TYNDP data will be read only for the given region_list).
Node_list = []
# Change region_list in mappings.py to include more/less nodes.
# ---------------------------------------------------------------------------
# all plants' lists and dictionaries (central and consumers') ---------------
# ---------------------------------------------------------------------------
# list of all plants (e.g. ['hp_ID300', 'ev_ID300'])
Plant_list = []

# list of all plants with inflow (e.g. ['dam_CH_01', 'psp_open_CH_01'])
Plant_inflow_list = []

# list of all plants with outflow (e.g. ['dam_CH_01', 'psp_open_CH_01'])
Plant_outflow_list = []

# list of all technologies (e.g. ['psp_open', 'hp', 'ev', 'pv'])
Tech_list = []

# dictionary of plant technologies (e.g. {'hp_ID300': 'hp', 'ev_ID300': 'ev'})
Map_plant_tech = {}

# dictionary of technologies and their plants (e.g. {'hp': ['hp_ID300'], 'ev': ['ev_ID300'], 'pv': ['pv_ID300']})
Map_tech_plant = {}

# dictionary of plant nodes (e.g. {'hp_ID300': 'CH_01', 'ev_ID300': 'CH_01'})
Map_plant_node = {}

Avail_plant = {}  # dictionary of available capacities for all plants

# dictionary of inflow data for all related plants, i.e. hydro plants (e.g. Inflow_data['dam_CH00', "t_1"]: 2]}), im MWh
Inflow_data = {}

Outflow_data = {}  # dictionary of inflow data for all related plants, e.g., EVs

# Infeed = {} # dictionary of Infeed data for all related plants. e.g., Infeed[node, tech, t] = 123.2 where node is nodes in the model, tech is in tech_infeed_list, t is the time step

# dictionary of Infeed data for all related consumers. Infeed_consumers[c,t]
Infeed_consumers = {}

# dictionary that assigns a    charging efficiency to each plant. This matters for plants with some sort of inflow to a storage (dam, PSP, battery, EV etc.) (e.g. {'ev_ID300': 0.9})
Map_eff_in_plant = {}

# dictionary that assigns a discharging efficiency to each plant. This matters for plants with some sort of outflow from a storage (dam, PSP, battery, EV etc.) (e.g. {'ev_ID300': 0.9})
Map_eff_out_plant = {}

Map_node_plant = {}
# determines for each node, the plants that are connected to it. Calculated based on Node_list Plant_list Map_plant_node. useful for constraints
# sample output Map_node_plant = {'CH_01': ['p_pv_1', 'p_gas_1', 'p_limited_energy_1'], 'EU_01': ['battery_1']}

# for each node, which plants are connected to that node - needs Node_list Plant_list Map_plant_node - useful for constraints - e.g., {'CH_01': ['consumer_01'], 'EU_01': ['consumer_02']}
Map_node_consumer = {}

# list of all plants that are not owned by active consumers (e.g. ['gas_AT00',...])
Plant_list_no_consumer = []

# dictionary that describes energy limited plants. The keys are plant (asset) names and values are generation within the time window (e.g. {'p_limited_energy_1': 0.0}). Later, more details should be included, e.g., several time windows (e.g. seasons) with given generation values.
Data_plant_energy_limited = {}

# dictionary that describes the start condition (between 0 1) of each (storage) plant. The keys are plant (asset) names and values are the start condition (e.g. {'AT00_dam': 0.05}). Later, more details should be included, e.g., several time windows (e.g. seasons) with given start conditions.
Plant_start_condition = {}
# Plant_start_condotion and Plant_end_condotion will be the same in an annual run.

# dictionary that describes the end   condition (between 0 1) of each (storage) plant. The keys are plant (asset) names and values are the end condition (e.g. {'AT00_dam': 0.95}). Later, more details should be included, e.g., several time windows (e.g. seasons) with given end conditions.
Plant_end_condition = {}
# Plant_start_condotion and Plant_end_condotion will be the same in an annual run.
# ---------------------------------------------------------------------------
# lists and dictionaries related to lines -----------------------------------
# ---------------------------------------------------------------------------
LineATC_list = []  # list of all lines (NTC and DC lines)

Map_line_node = {}  # dictionary of line nodes

# dictionary of export limits for all lines (trade from starting to end node) - must be non-negative
ATC_exportlimit = {}

# dictionary of import limits for all lines (trade from end to starting node) - must be non-negative
ATC_importlimit = {}

# determines for each node, the lines(ATC) are connected to it that are start node  - needs Map_line_node Node_list - useful for constraints
Map_node_exportinglineATC = {}
# sample output  for Map_line_node ={"line_01_CH01_EU01" : {"start_node": "CH_01", "end_node": "EU_01"}} - Map_node_exportinglineATC={'CH_01': ['line_01_CH01_EU01'], 'EU_01': []} - Map_node_importinglineATC = {'CH_01': [], 'EU_01': ['line_01_CH01_EU01']}

# determines for each node, the lines(ATC) are connected to it that are end node  - needs Map_line_node Node_list - useful for constraints
Map_node_importinglineATC = {}

# ---------------------------------------------------------------------------
# consumers' lists and dictionaries -----------------------------------------
# ---------------------------------------------------------------------------
# update all below with them=+netflex
Consumer_list = []  # list of all consumers (e.g. ['ID1', 'ID300'])

# dictionary for each consumer lists its assets (e.g. {'ID300': ['hp_ID300', 'ev_ID300', 'pv_ID300']})
Map_consumer_plant = {}

# dictionary for each consumer lists the node it is connected to (e.g. {'ID300': 'CH_01'})
Map_consumer_node = {}

# dictionary that assigns an optimization type to each consumer (either "maximize_utility" or "minimize_cost")
Map_consumer_optimization = {}

# dictionary that assigns a maximum import limit to each consumer (e.g. {'ID300': 20})
Consumer_import_max = {}

# dictionary that assigns a maximum export limit to each consumer (e.g. {'ID300': 20})
Consumer_export_max = {}

# dictionary that assigns a utility coefficient to each consumer's flexible demand.
Map_consumer_utilitycoeff = {}
# NOTE: The data abot Map_consumer_utilitycoeff should be added to consumer json files, and then read from them in the model.
# should be defined only if the Map_consumer_optimization[consumer]=="maximize_utility"
# utility[consumer][plant] = c0 + c1*(avg_plantconsumption) + c2*(avg_plantconsumption)^2
# the keys are consumer names. The values for every consumer are are dictionaries where the keys are plant names.
# The values for every plant are dictionaries where the keys are "constant", "a" and "b".
# The values for "constant", "a" and "b" are lists, where the length of the list is the number of time horizons defined for the plant (in Data_plant_flex_d_within_window[plant]["time_horizon"]).
# example Map_consumer_utilityfunction["consumer_01"]["hp_11"]["constant"][0] is the constant term of the utility function for the first time horizon of the heat pump "hp_11"  of the consumer "consumer_01"
# Map_consumer_utilitycoeff = {
#     "consumer_01" :
#         {"hp_11" :
#             {"c0": [0, 0, 0],
#             "c1": [10.1, 1.2, 10.3],
#             "c2": [-1, -1, -1]
#             },
#         "hp_12" :
#             {"c0": [0, 0],
#             "c1": [1.4, 1.5],
#             "c2": [-1, -1]
#             },

# dictionary that describes flexibility characteristics of flexible assets. The keys are plant (asset) names.
Data_plant_flex_d_within_window = {}
# The value will be another dictionary with keys "time_horizon" "energy" and "max_demand".
# this is useful for example for a heat pump that can only consume a certain amount of energy per day
# The values for "time_horizon" are lists of tuples (start, end) where start and end are integers between 1 and T.
# The values for "energy" and "max_demand" are lists of floats >= 0.

# dictionary consisting of consumers fixed demand for time steps (e.g. ["ID300","t_1"] = 1.1) in MW
Demand_data = {}

# original data set of demand from TYNDP (no correction applied)
Demand_data_TYNDP = {}

# dictionary consisting of consumers export (feed-in to the grid) tariff for time steps (e.g. ["ID300","t_1"] = 10) in EUR/MWh
tariff_export_hourly = {}

# dictionary consisting of consumers import (consumption) tariff for time steps (e.g. ["ID300","t_1"] = 20) in EUR/MWh
tariff_import_hourly = {}

# list of all consumers that have at least one plant (e.g. ['ID300'])
Consumer_list_with_plants = []

# totoal flex demand in each duration for each consumer (used in central model)
flex_demand_in_durations = {}

# ---------------------------------------------------------------------------
# to be possibly fixed in the model -----------------------------------------
# ---------------------------------------------------------------------------
# dictionary for all plants's names as keys and generation capacity in MW as values (e.g. { 'CH00_psp_open': 4000.0
Plant_capacity_gen = {}
# dictionary for all plants's names as keys and pumping capacity in MW as values (e.g. { 'CH00_psp_open': 4000.0
Plant_capacity_pmp = {}
# dictionary for all plants's names as keys and its direct storage capacity as values in MWh (e.g. { 'CH00_psp_open': 14000.0
Plant_capacity_strg = {}
# EV ----------------------------------------
# dictionary that to each EV plant assigns a maximum charging capacity
gen_max_EV_BT_data = {}
# dictionary that to each EV plant assigns a maximum discharging capacity
pmp_max_EV_BT_data = {}
# dictionary that to each EV plant assigns a maximum charging energy
gen_energy_max_EV_BT_data = {}

# list of infeed technologies used in the core run (e.g. ['pvrf', 'windon', 'windof']). If consumers' are decentrialized, this list should not include pv (that belongs to consuemrs).
tech_infeed_core_run_list = []

imported_all_consumers = {}
exported_all_consumers = {}
scenario_name = ""


Infeed_RES_TYNDP = {}

# The list of battery(ies) that replace a group of batteries owned by NETFLEX customers, only if single_large_battery is activated.
Plant_list_rep_bat = []
