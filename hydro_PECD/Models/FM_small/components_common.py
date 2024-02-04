import pyomo.environ as pyo
from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals
from structural_parameters import (
    Map_plant_tech_cost_component,
    tech_p_no_gen,
    tech_hydro_list,
    tech_store_list,
    tech_store_pump_list,
    tech_store_equal_pump_max_gen_max_list,
)
from structural_parameters import (
    tech_demand_assets_shiftable_netflex_list,
    cost_data_opr_slp,
    lostlost_cost,
    Start_condition_tech,
    cost_data_inv_gen_slp,
    cost_data_inv_e_slp,
    op_cost_n_tech_calibration,
    cost_data_opr_qdr,
)
from structural_parameters import (
    Map_eff_in_tech,
    Map_eff_out_tech,
)  # needed for core.py

# from settings_run import T_list, Node_list, Consumer_list_netflex, opt_mode
from data_prep.definitions_common import (
    Plant_start_condition,
    Plant_end_condition,
    Data_plant_energy_limited,
    LineATC_list,
    Demand_data,
    Map_plant_tech,
    Map_plant_node,
    Plant_inflow_list,
    Plant_outflow_list,
)
from data_prep.definitions_common import (
    Map_eff_in_plant,
    Map_eff_out_plant,
    Plant_list,
    Plant_start_condition,
    Outflow_data,
    Avail_plant,
    Map_consumer_optimization,
    Infeed_consumers,
    Map_node_plant,
    Map_node_consumer,
)
from data_prep.definitions_common import (
    Map_node_exportinglineATC,
    Map_node_importinglineATC,
    Data_plant_flex_d_within_window,
    ATC_importlimit,
    ATC_exportlimit,
)

# needed for core.py
from data_prep.definitions_common import (
    scenario_name,
    Map_line_node,
    Map_eff_in_plant,
    Map_eff_out_plant,
    Inflow_data,
)
from data_import_fcns import map_tech_to_plant
import time

# settings_scen = read_scenario_settings(scenario_name)
# T_list = settings_scen["T_list"]
# Node_list = settings_scen["Node_list"]
# Consumer_list_netflex = settings_scen["Consumer_list_netflex"]

# -----------------------------------------------------------------------------------------------------------
# --------------------------------------- define objective function -----------------------------------------
# -----------------------------------------------------------------------------------------------------------


def obj_expression(model):
    # investment cost to be defined over plants
    cost_inv = {}
    # operation cost to be defined over plants
    cost_op = {}

    for p in model.P:
        tech_typ_gen_e = Map_plant_tech_cost_component[Map_plant_tech[p]]
        if tech_typ_gen_e == "cap_op":
            # investment cost
            cost_inv[p] = model.investment_genmax_slp[p] * model.gen_max[p]

            # operation cost
            cost_op[p] = sum(
                [
                    # slope cost
                    model.operation_slp[p] * model.gen[p, t]
                    # quadratic cost
                    + model.operation_qdr[p] * model.gen[p, t] ** 2
                    for t in model.T
                    if p in model.P_gen
                ]
                # quadratic cost
            )
        elif tech_typ_gen_e == "cap_op_energy":
            # investment cost
            cost_inv[p] = (
                model.investment_genmax_slp[p] * model.gen_max[p]
                + model.investment_emax_slp[p] * model.gen_energy_max[p]
            )

            # operation cost
            cost_op[p] = sum(
                [
                    model.operation_slp[p] * model.gen[p, t]
                    for t in model.T
                    if p in model.P_gen
                ]
            )

    # lost load cost
    lostload_cost = sum(
        [
            model.lostload[c, tech, t] * model.lostload_cost[c]
            for c in model.Consumer
            for t in model.T
            for tech in model.Consumption_types_inflex
        ]
    )

    # slack cost
    if hasattr(model, "slack_soc") and model.slack_soc:
        slack_cost_coeff = 10000
        slack_cost = slack_cost_coeff * sum(
            model.slackSOC_POS[p, t] + model.slackSOC_NEG[p, t]
            for p in model.P_storage
            for t in model.T
        )
    else:
        slack_cost = 0
    return sum(cost_inv.values()) + sum(cost_op.values()) + lostload_cost + slack_cost


# -----------------------------------------------------------------------------------------------------------
# ----------------------------------------- define sets ----------------------------------------------------
# -----------------------------------------------------------------------------------------------------------


def define_sets(
    model,
    Plant_list_included,
    consumer_sel,
    consumer_infeed_sel,
    tech_infeed_selected,
    T_list,
    Node_list,
    Consumer_list_netflex,
    tech_demand_modeled,
    tech_demand_inflex_selected,
):
    """
    Define sets for the model (used in both for consumer runs and central runs).
    Inputs:
        model: pyomo model
        Plant_list_included: list of plants that are included in the model
        consumer_sel: list of consumers that are included in the model 
        consumer_infeed_sel: list of consumers that are included in the model and have infeed 
        - in central opt with direct load control: NETFLEX + TYNDP consumers
        - in consumer's individual opt: the consumer itself
        - in central run after consumer's individual opt: TYNDP consumers
        tech_infeed_selected: list of infeed technologies of consumers ("pv")
        T_list: list of time steps in the model
        Node_list: list of nodes in the model
        Consumer_list_netflex: list of consumers in NETFLEX
        tech_demand_modeled: list of demand side technologies that are included in the model (e.g., ["fixed", "hp", "v1g", "v2g"])
        tech_demand_inflex_selected: list of demand side technologies that are included in the model and are inflexible (e.g., ["fixed"])
    """
    model.T = Set(initialize=T_list, ordered=True, doc="time steps in the model")

    model.Node = Set(initialize=Node_list, doc="set of nodes")

    model.Consumer = Set(initialize=consumer_sel, doc=" set of consumers")

    model.Consumer_NETFLEX = Set(
        initialize=Consumer_list_netflex, doc=" set of <all> consumers in NETFLEX"
    )

    model.Consumer_with_infeed = Set(
        initialize=consumer_infeed_sel,
        within=model.Consumer,
        doc="set of consumers whose infeed is directly considered modeled in energy balance",
    )

    model.lineATC = Set(
        initialize=[
            l
            for l in LineATC_list
            if Map_line_node[l]["start_node"] in model.Node
            and Map_line_node[l]["end_node"] in model.Node
        ],
        doc="set of interconnections of ATC between regions",
    )

    model.P = Set(
        initialize=[p for p in Plant_list_included if Map_plant_node[p] in model.Node],
        doc="set of plants",
    )

    model.P_gen = Set(
        initialize=[p for p in model.P if Map_plant_tech[p] not in tech_p_no_gen],
        doc="set of plants that can generate",
    )
    model.P_hydro = Set(
        initialize=[p for p in model.P if Map_plant_tech[p] in tech_hydro_list],
        doc="set of hydro plants",
    )

    model.P_energymax = Set(
        initialize=[
            p
            for p in model.P
            if Map_plant_tech_cost_component[Map_plant_tech[p]] == "cap_op_energy"
        ],
        within=model.P,
        doc="plants with some sort of limit on energy, e.g., batteries and some biofules",
    )

    model.P_energylim = Set(
        initialize=[p for p in model.P if p in Data_plant_energy_limited.keys()],
        within=model.P,
        doc="plants with a limit on total production in a given period, e.g., some biofuels",
    )

    model.P_storage = Set(
        initialize=[p for p in model.P if Map_plant_tech[p] in tech_store_list],
        within=model.P,
        doc="set of storage plants",
    )

    model.P_ev = Set(
        initialize=[p for p in model.P if Map_plant_tech[p] in ["v1g", "v2g"]],
        within=model.P,
        doc="set of EV plants",
    )

    model.P_pumping = Set(
        initialize=[p for p in model.P if Map_plant_tech[p] in tech_store_pump_list],
        within=model.P,
        doc="set of storage plants that can pump",
    )

    model.P_inflow = Set(
        initialize=[p for p in model.P if p in Plant_inflow_list],
        within=model.P_storage,
        doc="set of storage plants with inflow/outflow, e.g., of type hydro or EV",
    )

    model.P_outflow = Set(
        initialize=[p for p in model.P if p in Plant_outflow_list],
        within=model.P_storage,
        doc="set of storage plants with inflow/outflow, e.g., of type hydro or EV",
    )

    model.P_equal_p_g_max = Set(
        initialize=[
            p
            for p in model.P
            if Map_plant_tech[p] in tech_store_equal_pump_max_gen_max_list
        ],
        within=model.P_storage,
        doc="set of storage plants that will have equal pumping and generating capacity",
    )

    model.P_flex_d_within_window = Set(
        initialize=[
            p
            for p in model.P
            if Map_plant_tech[p] in tech_demand_assets_shiftable_netflex_list
        ],
        within=model.P_pumping,
        doc="set of storage plants that can flexibly discharge within a given time window",
    )

    # defined as a list of unique values in the dictionary Map_plant_tech for the keys 'p' in model.P
    model.Tech_gen = Set(
        initialize=list(
            set(Map_plant_tech[key] for key in model.P if key in Map_plant_tech)
        ),
        doc="set of technologies that are in the model and can generate (no infeed technology)",
    )

    model.Tech_hydro = Set(
        initialize=tech_hydro_list, doc="set of technologies that are hydro"
    )
    model.Tech_infeed = Set(
        initialize=tech_infeed_selected,
        doc="set of technologies that can be used for infeed to consumers",
    )

    # model.Consumption_times_series_types = Set(
    #     initialize=tech_demand_time_series,
    #     doc="set of consuming technologies/types that have time series and will be saved in model.demand (not always used in the model)",
    # )
    model.Consumption_types = Set(
        initialize=tech_demand_modeled,
        doc="set of consuming technologies/types (e.g., in NETFLEX mode, fixed and ev etc. and in core, fixed country demand)",
    )
    
    model.Consumption_types_inflex = Set(
        initialize=tech_demand_inflex_selected,
        within=model.Consumption_types,
        doc="set of consuming technologies/types whose demand are fixed to input data",
    )
    # model.Consumption_types_flex = Set(
    #     initialize=[
    #         tech
    #         for tech in model.Consumption_types
    #         if tech not in model.Consumption_types_inflex
    #     ],
    #     within=model.Consumption_types,
    #     doc="set of consuming technologies/types whose demand are flexible",
    # )


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------------- define parameters -------------------------------------------------
# --------------------------------------------------------------------------------------------------------------


def define_params_op(model):
    """
    Define parameters for the model as attributes (used in both for consumer runs and central runs).
    Inputs:
        model: pyomo model
    """
    model.demand = Param(
        model.Consumer,
        model.Consumption_types_inflex,
        model.T,
        initialize=lambda model, consumer, tech, t: Demand_data[(consumer, tech, t)],
        doc="demand time series per consumer and time step",
    )

    model.operation_slp = Param(
        model.P_gen,
        initialize={
            p: cost_data_opr_slp[Map_plant_tech[p]]
            * (
                # if p has a slope cost of 0, calibration to country values do not matter, so we set it to 0
                op_cost_n_tech_calibration[Map_plant_node[p], Map_plant_tech[p]]
                if cost_data_opr_slp[Map_plant_tech[p]] > 0
                else 0
            )
            for p in model.P_gen
        },
    )

    model.operation_qdr = Param(
        model.P_gen,
        initialize={p: cost_data_opr_qdr[Map_plant_tech[p]] for p in model.P_gen},
    )

    # TODO: {} should be changed to Map_eff_in_plant
    Map_eff_in_plant = map_tech_to_plant(
        Plant_list, {}, Map_eff_in_tech, Map_plant_tech
    )

    # TODO: {} should be changed to Map_eff_out_plant
    Map_eff_out_plant = map_tech_to_plant(
        Plant_list, {}, Map_eff_out_tech, Map_plant_tech
    )

    model.storage_charge_eff_in = Param(
        model.P_storage,
        initialize={p: Map_eff_in_plant[p] for p in model.P_storage},
        doc="efficiency while    charging ([0,1])",
    )

    model.storage_charge_eff_out = Param(
        model.P_storage,
        initialize={p: Map_eff_out_plant[p] for p in model.P_storage},
        doc="efficiency while discharging ([0,1])",
    )

    # TODO: {} should be changed to Plant_start_condition
    Plant_start_condition = map_tech_to_plant(
        Plant_list, {}, Start_condition_tech, Map_plant_tech
    )

    model.storage_start_cond = Param(
        model.P_storage,
        initialize={p: Plant_start_condition[p] for p in model.P_storage},
        doc="initial/end state of charge ([0,1])",
    )

    model.inflow = Param(
        model.P_inflow,
        model.T,
        initialize={(p, t): Inflow_data[p, t] for p in model.P_inflow for t in model.T},
        doc="inflows from storage plants (MWh",
    )

    model.outflow = Param(
        model.P_outflow,
        model.T,
        initialize={
            (p, t): Outflow_data[p, t] for p in model.P_outflow for t in model.T
        },
        doc="outflows from storage plants (MWh",
    )  # adjust set to analyze only EVs and similar

    model.avail_plant = Param(
        model.P,
        model.T,
        initialize={(p, t): Avail_plant[p, t] for p in model.P for t in model.T},
        doc="availability of plants ([0,1])]",
    )

    model.energy_max = Param(
        model.P_energylim,
        model.T,
        initialize={
            (p, t): Data_plant_energy_limited[p]
            for p in model.P_energylim
            for t in model.T
        },
        doc="maximum energy production in a given period (MWh",
    )

    model.optimization_type = Param(
        model.Consumer,
        initialize={c: Map_consumer_optimization.get(c, "NA") for c in model.Consumer},
        doc="minimize_cost or maximize_utility for NETFLEX consumers, NA for other consumers",
    )

    model.infeed = Param(
        model.Consumer_with_infeed,
        model.Tech_infeed,
        model.T,
        initialize=lambda model, n, tech, t: Infeed_consumers.get((n, tech, t), 0)
        if (n, tech, t) in Infeed_consumers
        else 0,
        doc="fixed sum of infeed from e.g. PVs (MWh), 0 infeed if a consumer has no value in Infeed_consumers",
    )

    model.lostload_cost = Param(
        model.Consumer,
        initialize=lostlost_cost,
        doc="cost of lost load (EUR/MWh), 0 if a consumer has no value in Lostload_cost",
    )

    model.Map_node_plant = Param(
        model.Node, initialize={n: Map_node_plant[n] for n in model.Node}, doc="map of plants to nodes"
    )

    model.Map_node_consumer = Param(
        model.Node, initialize={n: Map_node_consumer[n] for n in model.Node}, doc="map of consumers to nodes"
    )

    model.Map_node_exportinglineATC = Param(
        model.Node,
        initialize={n: Map_node_exportinglineATC[n] for n in model.Node},
        doc="map of nodes to exporting lines",
    )

    model.Map_node_importinglineATC = Param(
        model.Node,
        initialize={n: Map_node_importinglineATC[n] for n in model.Node},
        doc="map of nodes to importing lines",
    )

    model.Map_plant_tech = Param(
        model.P, initialize={p: Map_plant_tech[p] for p in model.P}, doc="map of plants"
    )

    model.Data_plant_flex_d_within_window = Param(
        model.P_flex_d_within_window,
        initialize={
            p: Data_plant_flex_d_within_window[p] for p in model.P_flex_d_within_window
        },
        doc="flexibility of plants within a given time window (MWh)",
    )
    
    model.sum_generation_plant_energy_limited = Param(
        model.P_energylim,
        initialize={p: Data_plant_energy_limited[p] for p in model.P_energylim},
        doc="sum of energy limited generation (MWh)",
    )


def define_params_inv(model):
    """
    Define investment cost parameters for the model as attributes.
    """
    model.investment_genmax_slp = Param(
        model.P,
        initialize={p: cost_data_inv_gen_slp[Map_plant_tech[p]] for p in model.P},
    )
    
    model.investment_emax_slp = Param(
        model.P_energymax,
        initialize={
            p: cost_data_inv_e_slp[Map_plant_tech[p]] for p in model.P_energymax
        },
    )


# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------ define variables ---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------


def define_vars_op(model):
    """
    Define variables for the model as attributes (used in both for consumer runs and central runs).
    Inputs:
        model: pyomo model
    """
    model.gen = Var(
        model.P_gen,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="generation (discharge of storage plant) (MWh)",
    )

    model.soc = Var(
        model.P_storage,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="state of the charge (MWh)",
    )

    model.storage_charge = Var(
        model.P_pumping,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="energy used to charge storage plant p in t (MWh) - charging or pumping",
    )
    
    model.exported = Var(
        model.Consumer,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="consumer's exported value (MWh)",
    )

    model.imported = Var(
        model.Consumer,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="consumer's imported value (MWh)",
    )

    model.lostload = Var(
        model.Consumer,
        model.Consumption_types,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="lost load of consumers (MWh) ",
    )

    model.curtailment = Var(
        model.Consumer_with_infeed,
        model.T,
        domain=NonNegativeReals,
        initialize=0,
        doc="consumers' curtailment of RES generation (MWh) - used in consumer optimization",
    )

    if hasattr(model, "slack_soc") and model.slack_soc:
        print("slack_soc is True ...................... defining SOC slack variables")
        model.slackSOC_POS = Var(
            model.P_storage,
            model.T,
            initialize=0,
            domain=NonNegativeReals,
            doc="positive slack variable for storeBalance_Constraint",
        )
        
        model.slackSOC_NEG = Var(
            model.P_storage,
            model.T,
            initialize=0,
            domain=NonNegativeReals,
            doc="negative slack variable for storeBalance_Constraint",
        )


    model.spill_water = Var(
        model.P_hydro,
        model.T,
        initialize=0,
        domain=NonNegativeReals,
        doc="slack variable allowing for spilling water in hydro plants to avoid infeasibility caused by storage capacity limit",
    )
    # model.curtail_node      = Var(model.Node,       model.T, domain=NonNegativeReals, initialize=0, doc= "nodes' curtailment of RES generation (MWh) - used for neighbours' nodes that have no consumer")


def define_vars_inv(model):
    """
    Define investment (generation and energy capacities) variables for the model as attributes (used in both for consumer runs and central runs).
    """
    model.gen_max = Var(
        model.P,
        domain=NonNegativeReals,
        initialize=0,
        doc="maximum generation capacity (MW)",
    )

    model.pmp_max = Var(
        model.P_pumping,
        domain=NonNegativeReals,
        initialize=0,
        doc="maximum pumping capacity (MW)",
    )

    model.gen_energy_max = Var(
        model.P_energymax,
        domain=NonNegativeReals,
        initialize=0,
        doc="maximum storable energy (MWh) in a period/at each time step, for batteries it gives max soc, for biofuels it gives maximum energy avilable",
    )


# ---------------------------------------------------------------------------------------------------------------
# ---------------------------------------------- define constraints --------------------------------------------
# ---------------------------------------------------------------------------------------------------------------


def define_constraints(model):
    """
    Define constraints for the model as attributes (used in both for consumer runs and central runs).
    Inputs:
        model: pyomo model
    """

    print("defining constraints")
    # Generation limit
    start = time.time()
    model.generation_limit = Constraint(
        model.P_gen, model.T, rule=generation_limit_Constraint
    )
    print("generation_limit took: ", time.time() - start, " seconds")

    # Storage (battery/closed pump storage/hydrogen)
    start = time.time()
    model.storage_soc = Constraint(
        model.P_storage, model.T, rule=storeBalance_Constraint
    )
    print("storage_soc took: ", time.time() - start, " seconds")

    # Storage start condition
    start = time.time()
    model.storage_start_condition = Constraint(
        model.P_storage, rule=storage_start_condition_Constraint
    )  
    print("storage_start_condition took: ", time.time() - start, " seconds")

    # Charge power limit (discharg/generation power is taken care of in generation_limit_Constraint)
    start = time.time()
    model.storage_rate_limit = Constraint(
        model.P_pumping, model.T, rule=storage_charge_Constraint
    )
    print("storage_rate_limit took: ", time.time() - start, " seconds")

    # equalizing the maximum generation capacity and the maximum charging rate
    start = time.time()
    model.p_max_limit = Constraint(model.P_equal_p_g_max, rule=p_max_limit_Constraint)
    print("p_max_limit took: ", time.time() - start, " seconds")

    # energy limit of a storage plant  --- for limited energy technologies, we have energy_limit_Constraint
    start = time.time()
    model.storage_soc_limit = Constraint(
        model.P_storage, model.T, rule=storage_soc_Constraint
    )
    print("storage_soc_limit took: ", time.time() - start, " seconds")

    # Lost load limit, so far, its defined to be <model.demand[c,t] ,i.e., the fixed demand of the consumer
    start = time.time()
    model.lostload_limit = Constraint(
        model.Consumer,
        model.Consumption_types_inflex,
        model.T,
        rule=lostload_limit_Constraint,
    )
    print("lostload_limit took: ", time.time() - start, " seconds")

    # Curtailment limit
    start = time.time()
    model.curtailment_limit = Constraint(
        model.Consumer_with_infeed, model.T, rule=curtailment_limit_Constraint
    )
    print("curtailment_limit took: ", time.time() - start, " seconds")
    
    # Energy limit for limited_energy techs
    start = time.time()
    model.energy_limit = Constraint(
        model.P_energylim, rule=energy_limit_Constraint
    )  
    print("energy_limit took: ", time.time() - start, " seconds")


# NOTE: activate lines below, only if for energy limited technologies, you want to limit sum of generation for multiple periods within a year
# # Generation limit for limited_energy techs ---------------------------------------------------------------
# # for every plant in P_energylim, and for every duration in form of tupple stored in Map_plant_duration[plant]["time_horizon"], we have a constraint that limits the energy stored in the plant
# # assuming you have already created your Pyomo model as 'model'
# for p, data in Data_plant_energy_limited.items():
#     if p in model.P_energylim:
#         for i, time_range in enumerate(data["time_horizon"]):
#             start, end = time_range
#             energy_limit = data["energy"][i]
#             # create the constraint
#             model.add_component(
#                 f"energy_limit_{p}_{i}",
#                 Constraint(
#                     expr=sum(model.gen[p, "t_" + str(t)] for t in range(
#                         start, end+1)) <= model.gen_energy_max[p]*energy_limit
#                 )
#             )


# ---------------------------------------------------------------------------------------------------------------
# ---------------------------------------------- constraints equations -----------------------------------------
# ---------------------------------------------------------------------------------------------------------------


# find the intersectino of a and b
def intersection(a, b):
    return list(set(a) & set(b))


# define a function that gets a list with several elements that are all strings, and returns the input if the input has multiple elements and returns [element] if the input has only one element


def list_to_list(input):
    if type(input) == list:
        return input
    else:
        return [input]


# energy balance


def energy_balance_Constraint(model, t, n):
    # generatin from all technologies
    gen = sum(model.gen[p, t] for p in model.P_gen & model.Map_node_plant[n])
    # infeed from RES infeed technologies
    infeed = sum(
        model.infeed[c, tech, t]
        for c in model.Consumer_with_infeed & model.Map_node_consumer[n]
        for tech in model.Tech_infeed
    )
    demand_fixed = sum(
        model.demand[c, tech, t]
        for c in model.Consumer & model.Map_node_consumer[n]
        for tech in model.Consumption_types_inflex
    )
    # demand from all storage technologies, which includes pumping and charging etc.
    demand_storage = sum(
        model.storage_charge[p, t] for p in model.P_pumping & model.Map_node_plant[n]
    )
    lostload = sum(
        model.lostload[c, tech, t]
        for c in model.Consumer & model.Map_node_consumer[n]
        for tech in model.Consumption_types_inflex
    )
    # positive means export, negative means import
    export_as_starting_node = sum(
        model.Export[l, t] for l in model.lineATC & model.Map_node_exportinglineATC[n]
    )
    # positive means import, negative means export
    import_as_ending_node = sum(
        model.Export[l, t] for l in model.lineATC & model.Map_node_importinglineATC[n]
    )
    # curtailment from all curtailment technologies
    curtailment = sum(
        model.curtailment[c, t]
        for c in model.Consumer_with_infeed & model.Map_node_consumer[n]
    )
    return (
        gen + infeed + import_as_ending_node + lostload
        == demand_fixed + demand_storage + export_as_starting_node + curtailment
    )


# Generation limit


def generation_limit_Constraint(model, p, t):
    return model.gen[p, t] <= (model.gen_max[p] * model.avail_plant[p, t])


# Storage (battery/closed pump storage/hydrogen)


def storeBalance_Constraint(model, p, t):
    # state of charge at t
    soc_t = model.soc[p, t]

    # state of charge at t-1
    soc_t_1 = model.soc[p, model.T.prevw(t)]

    # energy charged to the plant via pumping (only for specific plants model.P_pumping)
    charged = sum(
        [
            model.storage_charge[p, t] * model.storage_charge_eff_in[p]
            if p in model.P_pumping
            else 0
        ]
    )

    # energy discharged from the plant (plants with no generation are exluded, e.g., v1g EVs)
    discharged = sum(
        [model.gen[p, t] / model.storage_charge_eff_out[p] if p in model.P_gen else 0]
    )

    # inflow
    inflow = sum([model.inflow[p, t] if p in model.P_inflow else 0])

    # outflows
    outflow = sum([model.outflow[p, t] if p in model.P_outflow else 0])
    # if model.slack_soc exists and is True
    if hasattr(model, "slack_soc") and model.slack_soc:
        slack_pos = model.slackSOC_POS[p, t]
        slack_neg = model.slackSOC_NEG[p, t]
    else:
        slack_pos = 0
        slack_neg = 0

    # allow for spilling water
    spill_energy = sum([model.spill_water[p, t] if p in model.P_hydro else 0])


    return (
        soc_t + slack_neg
        == soc_t_1 + charged - discharged + inflow - outflow + slack_pos - spill_energy
    )


def storage_start_condition_Constraint(model, p):
    # Generally, initial conditions of storage plants are equality constraints to a percentage of their maximum energy. This ensures, e.g., hydro plants reservior follows actual patterns.
    # Except for EVs: to avoid unnecessary constraints (and infeasilbity), initial condition is defined as inequality.
    if p in model.P_ev:
        return (
            model.soc[p, model.T.at(1)]
            <= model.storage_start_cond[p] * model.gen_energy_max[p]
        )
    else:
        return (
            model.soc[p, model.T.at(1)]
            == model.storage_start_cond[p] * model.gen_energy_max[p]
        )


# Storage end condition


# def storage_end_condition_Constraint(model, p):
#     return (
#         model.soc[p, model.T.at(-1)]
#         == model.storage_end_cond[p] * model.gen_energy_max[p]
#     )


# charge power limit (discharg/generation power is taken care of in generation_limit_Constraint)


def storage_charge_Constraint(model, p, t):
    if Map_plant_tech[p] in tech_demand_assets_shiftable_netflex_list:
        pmp_max_fixed = Data_plant_flex_d_within_window[p]["max_demand"]
        return model.storage_charge[p, t] <= (pmp_max_fixed * model.avail_plant[p, t])
    else:
        return model.storage_charge[p, t] <= (
            model.pmp_max[p] * model.avail_plant[p, t]
        )


# equalizing the maximum generation capacity and the maximum charging rate


def p_max_limit_Constraint(model, p):
    return model.pmp_max[p] <= model.gen_max[p]


# energy limit of a storage plant  --- for limited energy technologies, we have energy_limit_Constraint


def storage_soc_Constraint(model, p, t):
    return model.soc[p, t] <= model.gen_energy_max[p]


# Generation limit for limited_energy techs --- for storage technologies, we have storage_soc_Constraint


def energy_limit_Constraint(model, p):
    return (
        sum([model.gen[p, t] for t in model.T])
        <= model.sum_generation_plant_energy_limited[p] * len(model.T) / 8760
    )


# NOTE: if multiple periods within a year is to be considered, then len(model.T)/8760 above should be adjusted.


# line limits


def ATCbound_Constraint(model, l, t):
    return (-ATC_importlimit[l, t], model.Export[l, t], ATC_exportlimit[l, t])


def consumer_import_Constraint(model, c, t):
    return model.imported[c, t] <= model.consumer_import_max[c, t]


def consumer_export_Constraint(model, c, t):
    return model.exported[c, t] <= model.consumer_export_max[c, t]


def lostload_limit_Constraint(model, c, tech, t):
    # if demand is positive (consuming), then lostload must be less than demand
    # if demand is negative (generating, e.g., in the case of consumers), then max(0,demand) allows lostload to be 0...
    # ... which is necessary because lostload is defined as a non-negative variable.
    return model.lostload[c, tech, t] <= max(model.demand[c, tech, t], 0)


def curtailment_limit_Constraint(model, c, t):
    # if sum or RES generation is positive (generating), then curtailment must be less than sum of RES generation.
    # if sum of RES generation is negative (which should not be possible), then max(0,sum(RES generation)) allows crutailment to be 0...
    # ... which is necessary because curtailment is defined as a non-negative variable.
    # NOTE: this should be later be avoided, by making sure that sum of RES generation is always positive, even after substracting consumers' infeed from main infeed.
    return model.curtailment[c, t] <= max(
        0, sum(model.infeed[c, tech, t] for tech in model.Tech_infeed)
    )


# ---------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- fixing values ----------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
# write a function that gets a model and target_variable and a subset of target_variable and a list of values for the subset and fixes the values of the target_variable to the values in the list


def fix_variable(model, target_variable, subset, values):
    for i, v in enumerate(subset):
        model.__getattribute__(target_variable)[v] = values[i]


# def fix_variables(model, target_variable, target_subset, target_values):
#     target_variable_within_target_subset = {model.variable_to_be_fixed[element]: element for element in target_subset}  # Example fixed values
#     for var in model.target_variable:
#         if var in target_variable_within_target_subset:
#             var.fix(target_variable_within_target_subset[value])


def fix_variables(target_variable, subset, target_values):
    """
    Fixes the values of a "subset" of a "target_variable" that are exogenously given by values stored in "target_values".
    Inputs:
        target_variable: the variable to be fixed (e.g. model.gen_max)
        subset: the subset of target_variable (e.g., EV cars)
        target_values: the values of the target_variable (e.g., 0.11 MW)

    :return: the model with fixed target_variable
    """
    for element in subset:
        target_variable[element].fix(target_values[element])
    return target_variable
