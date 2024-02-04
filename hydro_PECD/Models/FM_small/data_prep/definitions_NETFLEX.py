# ------------------------------------------------------------------------
# define parameters for the consumers ------------------------------------
# ------------------------------------------------------------------------

# list of all assets of the consumers (e.g. [... 'hp_ID300', 'ev_ID300', 'pv_ID300'])
Plant_list_netflex = []

# dictionary that assigns a technology to each asset of the consumers (e.g. {'hp_ID300': 'hp', 'ev_ID300': 'ev', 'pv_ID300': 'pv'})
Map_plant_tech_consumer_netflex = {}

# dictionary that assigns a node to each asset of the consumers (e.g. {'hp_ID300': 'CH_01', 'ev_ID300': 'CH_01', 'pv_ID300': 'CH_01'})
Map_plant_node_consumer_netflex = {}

# dictionary that indicates whether a plant is available for dispatch or not. 1=available, 0=not available, 0< <1=partially available.
Avail_plant_consumer_netflex = {}

Map_consumer_plant_netflex = {}

Map_consumer_node_netflex = {}

# dictionary that assigns an optimization type to each consumer (either "maximize_utility" or "minimize_cost")
Map_consumer_optimization_netflex = {}

# dictionary that assigns a maximum import limit to each consumer
Consumer_import_max_netflex = {}

# dictionary that assigns a maximum export limit to each consumer
Consumer_export_max_netflex = {}

# dictionary that describes flexibility characteristics of flexible demand such as time_horizon energy and max_demand
Data_plant_flex_d_within_window_netflex = {}

# dictionary that assigns a time series of Infeed to each consumer. (consumer, t): 10
Infeed_consumer_netflex = {}

# dictionary that assigns a demand time series to each consumer and type of demand. (consumer_ID, techs, t): 10 (techs defined in tech_demand_with_timeseries_netflex_list)
Demand_data_consumer_netflex = {}

# dictionary of time series of generation/consumption of plants (owned by consumers) that might be flexible
Demand_data_flexible_consumer_netflex = {}

# dictionary that assigns a    charging efficiency to each plant. This matters for plants with some sort of inflow to a storage (dam, PSP, battery, EV etc.)
Map_eff_in_plant_netflex = {}

# dictionary that assigns a discharging efficiency to each plant. This matters for plants with some sort of outflow from a storage (  PSP, battery, EV etc.)
Map_eff_out_plant_netflex = {}

# dictionary that assigns a time series of outflow to each EV plant
Outflow_data_ev_netflex = {}

Plant_outflow_list_netflex = []    # list of plants with outflow data from NETFLEX

# dictionary that assigns a maximum charging capacity to each EV plant or batteries
gen_max_EV_BT_data_netflex = {}

# dictionary that assigns a maximum discharging capacity to each EV plant or batteries
pmp_max_EV_BT_data_netflex = {}

# dictionary that assigns a maximum charging energy to each EV plant or batteries
gen_energy_max_EV_BT_data_netflex = {}


# dictionary that assigns a time series of total demand (aggregate demand of all consumers) to each time step t, e.g., Demand_NETFLEX_sum['t_1'] = 10
Demand_NETFLEX_sum_instance = {}

# dictionary that assigns a time series of total infeed (aggregate infeed of all consumers) to each time step t. e.g. Infeed_NETFLEX_sum['t_1'] = 10
Infeed_NETFLEX_sum_instance = {}
