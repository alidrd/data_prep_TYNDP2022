from pyomo.environ import Constraint, Param, Set, Var
from data_prep.data_import_NETFLEX import Data_plant_flex_d_within_window

# -----------------------------------------------------------------------------------------------------------
# --------------------------------------- define objective function -----------------------------------------
# -----------------------------------------------------------------------------------------------------------


def obj_expression_consumer(model):
    """
    Define objective function for consumers as sum of utility gains minus net payments for imported energy and lost load costs.
    Inputs:
        - model: Pyomo model
    """

    # TODO: when utilty maximization activated, Map_consumer_utilitycoeff should be imported from data_import_NETFLEX
    # TODO: remove the line below
    from data_prep.definitions_common import Map_consumer_utilitycoeff

    payment = sum(
        (
            model.imported[c, t] * model.tariff_import[c, t]
            - model.exported[c, t] * model.tariff_export[c, t]
        )
        for t in model.T
        for c in model.Consumer
    )

    lostload_costs = sum(
        model.lostload[c, tech, t] * model.lostload_cost[c]
        for t in model.T
        for c in model.Consumer
        for tech in model.Consumption_types_inflex
    )

    utility_gain = 0
    for c in model.Consumer:
        if model.optimization_type[c] == "minimize_cost":
            utility_gain = 0
        elif model.optimization_type[c] == "maximize_utility":
            for p in model.P_pumping & Data_plant_flex_d_within_window.keys():
                for i, time_range in enumerate(
                    Data_plant_flex_d_within_window[p]["time_horizon"]
                ):
                    n = i + 1
                    utility_gain = (
                        utility_gain
                        + Map_consumer_utilitycoeff[c][p]["c0"][i]
                        + Map_consumer_utilitycoeff[c][p]["c1"][i]
                        * model.flex_demand_in_durations[(c, p, n)]
                    )  # +  Map_consumer_utilitycoeff[c][p]["c2"][i] * model.flex_demand_in_durations[(c,p,n)]**2
                    # TODO: activate the line above. Somehow, it does not work and leads to the error:
                    # RuntimeError: Cannot write legal LP file.  Objective 'OBJ' has nonlinear terms that are not quadratic.
                    # Even though the objective function is quadratic, it is not recognized as such by Pyomo.
    
    utility = utility_gain - payment - lostload_costs

    return utility

# ------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- define constraints -----------------------------------------
# ------------------------------------------------------------------------------------------------------------


def energy_balance_Constraint_consumer(model, c, t):
    # infeed from all infeed plants (PV)
    infeed = sum(
        model.infeed[c, tech, t]
        for c in model.Consumer_with_infeed
        for tech in model.Tech_infeed
    )
    # generation from all technologies
    gen = sum(model.gen[p, t] for p in model.P_gen)
    demand_fixed = sum(
        model.demand[c, tech, t]
        for c in model.Consumer
        for tech in model.Consumption_types_inflex
    )
    demand_storage = sum(model.storage_charge[p, t] for p in model.P_pumping)
    lostload = sum(
        model.lostload[c, tech, t] for tech in model.Consumption_types_inflex
    )
    return (
        infeed + gen + model.imported[c, t] + lostload
        == demand_fixed
        + demand_storage
        + model.exported[c, t]
        + model.curtailment[c, t]
    )


def define_constraints_consumer(model):
    """
    Define constraints specific to consumers.
    Inputs:
        - model: Pyomo model
    """
    # Minimum total consumption limit for flexible demand in form of flex_d_within_window -------------------------------------
    for c in model.Consumer:
        if model.optimization_type[c] == "minimize_cost":
            for p in model.P_flex_d_within_window:
                data = Data_plant_flex_d_within_window[p]
                for i, time_range in enumerate(data["time_horizon"]):
                    n = i + 1
                    start, end = time_range
                    # check if time range is within the time horizon of the model
                    if "t_" + str(start) in model.T and "t_" + str(end) in model.T:
                        energy_limit = data["energy"][i]
                        # create the constraint
                        model.add_component(
                            f"consume_tot_limit_{p}_{n}",
                            Constraint(
                                # TODO: range(start, end+1) does not work if start > end (jumping over last hour of the year, t_8760)
                                expr=sum(
                                    model.storage_charge[p, "t_" + str(t)]
                                    for t in range(start, end + 1)
                                )
                                == energy_limit
                            ),
                        )
        elif model.optimization_type[c] == "maximize_utility":
            continue  # no such constraints needed for utility maximization, as total consumption is deciced by the utility function


# ------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- define parameters  -----------------------------------------
# ------------------------------------------------------------------------------------------------------------
def define_params_consumer(
    model,
    tariff_import_data,
    tariff_export_data,
    Consumer_import_max,
    Consumer_export_max,
    Map_consumer_optimization_c,
    Map_consumer_plant_c,
):
    """
    Define parameters for consumers.
    Inputs:
        - model: Pyomo model
        - tariff_import_data: dictionary with tariff for importing from the grid (?/MWh) for each consumer and each time step.
        - tariff_export_data: dictionary with tariff for exporting generation to the grid (?/MWh) for each consumer and each time step.
        - Consumer_import_max: dictionary with maximum import capacity (fuesbox limit) for each consumer and each time step (MW?KW?).
        - Consumer_export_max: dictionary with maximum export capacity (fuesbox limit) for each consumer and each time step (MW?KW?).
        - Map_consumer_optimization_c: dictionary with optimization type for each consumer (cost minimization or utility maximization).
        - Map_consumer_plant_c: dictionary with plants owned by each consumer.
    """
    model.tariff_import = Param(
        model.Consumer,
        model.T,
        initialize={
            (c, t): tariff_import_data[c, t] for c in model.Consumer for t in model.T
        },
        doc="tariff for consumers (EUR/MWh), while importing from the grid",
    )

    model.tariff_export = Param(
        model.Consumer,
        model.T,
        initialize={
            (c, t): tariff_export_data[c, t] for c in model.Consumer for t in model.T
        },
        doc="tariff for consumers (EUR/MWh), while exporting to the grid",
    )

    model.consumer_import_max = Param(
        model.Consumer,
        model.T,
        initialize={
            (c, t): Consumer_import_max[c] for c in model.Consumer for t in model.T
        },
        doc="maximum import for consumers (MWh)",
    )
    
    model.consumer_export_max = Param(
        model.Consumer,
        model.T,
        initialize={
            (c, t): Consumer_export_max[c] for c in model.Consumer for t in model.T
        },
        doc="maximum export for consumers (MWh)",
    )


# ------------------------------------------------------------------------------------------------------------
# --------------------------- define sets and parameters for utility maximization ----------------------------
# ------------------------------------------------------------------------------------------------------------


def define_sets_vars_params_consumer_utility_max(model):
    """
    Define flexibility-related sets, variables and parameters as attributes of the model for consumers.
    Inputs:
        - model: Pyomo model
    """

    
    # finding max length of time horizon of plants owned by all consumers (to define sets and variables)
    max_length = 0
    for c in model.Consumer:
        if model.optimization_type[c] == "maximize_utility":
            for p in model.P_pumping & Data_plant_flex_d_within_window.keys():
                if len(Data_plant_flex_d_within_window[p]["time_horizon"]) > max_length:
                    max_length = len(Data_plant_flex_d_within_window[p]["time_horizon"])

    # sets ---------------------------------------------------
    model.D_flex_demand = Set(
        initialize=range(1, max_length + 1),
        doc="set of (max number of) time periods within the time horizon of the plants ownded by the consumer",
    )

    model.P_pumping_flex = Set(
        within=model.P_pumping,
        initialize=lambda model: model.P_pumping
        & Data_plant_flex_d_within_window.keys(),
        doc="set of plants with flexible demand",
    )

    # variables
    model.flex_demand_in_durations = Var(
        model.Consumer,
        model.P_pumping_flex,
        model.D_flex_demand,
        initialize=0,
        doc="flexible demand in each time period of the time horizon of the plants ownded by the consumer",
    )
    
    # constraint----------------------------------------------
    for c in model.Consumer:
        if model.optimization_type[c] == "maximize_utility":
            for p in model.P_pumping & Data_plant_flex_d_within_window.keys():
                for i, time_range in enumerate(
                    Data_plant_flex_d_within_window[p]["time_horizon"]
                ):
                    n = i + 1
                    start, end = time_range
                    model.add_component(
                        f"consume_tot_limit_{c}_{p}_{n}",
                        Constraint(
                            expr=model.flex_demand_in_durations[(c, p, n)]
                            == sum(
                                model.storage_charge[p, "t_" + str(t)]
                                for t in range(start, end + 1)
                            )
                        ),
                    )
