from data_prep.definitions_common import *
import data_prep.definitions_common
from data_prep.definitions_NETFLEX import *
from data_prep.definitions_TYNDP import *
from data_prep.definitions_TYNDP import Consumer_list_TYNDP
from data_prep.data_import_TYNDP import data_import_TYNDP_fcn
from data_prep.data_import_NETFLEX import data_import_NETFLEX_fcn
from components_common import *
from components_central import *
from read_settings import read_scenario_settings
from reset_items import get_lists_and_dicts
from pyomo.opt import ProblemFormat
from consumer_scale_up import consumer_demand_scale, consumer_asset_demand_scale

from correct_CH_demand_infeed import correct_CH_demand_infeed_fcn
from utils.utilities_model import export_model_to_txt
from utils.dict_to_csv import dict_3dim_to_csv
import aggregation.results_export as res_export

# %% import packages ---------------------------------------------------------------------------------
from pydoc import doc
import pyomo.environ as pyo
import pandas as pd
from io import StringIO  # used to export model to txt file
import time
import os

from consumers_opt import consumers_opt_fcn
from structural_parameters import (
    tech_demand_with_timeseries_netflex_model_list,
    tech_infeed_consumers_list,
    tech_infeed_all_list,
)


def core_main(scenario_name):
    # read settings for the scenario ---------------------------------------------------------------------
    # TODO: if need be, define all settings in a single file/location
    settings_scen = read_scenario_settings(scenario_name)
    T_list = settings_scen["T_list"]
    Node_list = settings_scen["Node_list"]
    consumer_based_on_tariff = settings_scen["consumer_based_on_tariff"]
    Consumer_list_netflex = settings_scen["Consumer_list_netflex"]

    # number of consumers that each consumer in Consumer_list_netflex represents (e.g., 1, 2, 3, etc.)
    consumers_representing = settings_scen["consumers_representing"]
    slack_soc = settings_scen["slack_soc"]
    single_large_battery = settings_scen["single_large_battery"]
    winter_limit = settings_scen["winter_limit"]

    # data import, NETFLEX and TYNDP  --------------------------------------------------------------------
    data_import_NETFLEX_fcn(scenario_name)
    
    data_import_TYNDP_fcn(scenario_name)

    correct_CH_demand_infeed_fcn(
        consumers_representing,
        T_list,
        Consumer_list_netflex,
        tech_demand_with_timeseries_netflex_model_list,
        tech_infeed_consumers_list,
    )

    if not consumer_based_on_tariff:
        consumer_asset_demand_scale(
            consumers_representing, Consumer_list_netflex, T_list, single_large_battery
        )
    # running consumers optimization ---------------------------------------------------------------------
    if consumer_based_on_tariff:
        consumers_opt_fcn(scenario_name)

        # updating lists --------------------------------
        # from Plant_list, remove plants that are used by consumers in keys of imported_all_consumers
        for consumer in imported_all_consumers:
            for plant in Map_consumer_plant[consumer]:
                # if plant is not a fixed infeed technology, e.g. pv, wind, etc.
                if Map_plant_tech[plant] not in tech_infeed_consumers_list:
                    Plant_list.remove(plant)

        # if consumers acted based on pv plants (as opposed to pvrf) are owned by consumers and not by the central planner
        # tech_infeed_core_run_list is equal to tech_infeed_all_list with pv excluded
        tech_infeed_core_run_list = [
            element
            for element in tech_infeed_all_list
            if element not in tech_infeed_consumers_list
        ]
    else:
        tech_infeed_core_run_list = tech_infeed_all_list.copy()

    # running central part of core -----------------------------------------------------------------------
    print("Running central part of core_main for scenario: " + scenario_name + " .")

    if consumer_based_on_tariff:
        consumer_demand_scale(consumers_representing)

    # model definition ----------------------------------------------------------------------------------
    model = ConcreteModel(
        name="core_" + scenario_name + "_" + str(time.time()).split(".")[0]
    )

    if slack_soc:
        model.slack_soc = True

    define_sets(
        model,
        Plant_list,
        Consumer_list,  # both TYNDP and NETFLEX consumers
        Consumer_list_TYNDP
        if consumer_based_on_tariff
        else Consumer_list,  # consumer_infeed_sel
        tech_infeed_core_run_list,
        T_list,
        Node_list,
        Consumer_list_netflex,
        [
            "fixed",
        ],  # tech_demand_modeled #TODO: check if this is needed
        [
            "fixed",
        ],  # tech_demand_inflex_selected
    )
    # %% Parameters --------------------------------------------------------------------------------------
    Start = time.time()
    define_params_inv(model)
    define_params_op(model)
    print("time to define parameters: ", time.time() - Start)
    # %% Exporting the model to
    # export_model_to_txt("after_params_" + scenario_name, model)
    # %% Variables  --------------------------------------------------------------------------------------
    Start = time.time()
    define_vars_op(model)
    define_vars_inv(model)
    model.Export = Var(
        model.lineATC,
        model.T,
        domain=Reals,
        initialize=0,
        doc="exported value on a line (ATC) from start node to end node - negative values specify imports - (MWh)",
    )
    print("time to define variables: ", time.time() - Start)
    # %% Objective function ------------------------------------------------------------------------------
    start = time.time()
    model.OBJ = Objective(rule=obj_expression)
    print("time to define objective function: ", time.time() - start)
    # %% Constraints -------------------------------------------------------------------------------------
    start_ct = time.time()
    define_constraints(model)
    start_central = time.time()
    define_constraints_central(
        model,
        consumer_based_on_tariff,
        winter_limit,
    )
    print("time to define central constraints: ", time.time() - start_central)
    # energy balance
    start_balance = time.time()
    model.energy_balance = Constraint(
        model.T, model.Node, rule=energy_balance_Constraint
    )
    print("time to define energy balance constraints: ", time.time() - start_balance)

    # line limits
    start_ATC = time.time()
    model.lineATClimit = Constraint(model.lineATC, model.T, rule=ATCbound_Constraint)
    print("time to define ATC constraints: ", time.time() - start_ATC)
    print("time to define constraints: ", time.time() - start_ct)
    # %% fixing values ----------------------------------------------------------------------------------
    # fix values of EVs and batteries ---------------------------------
    if not consumer_based_on_tariff:
        start = time.time()
        Plant_list_EV_BT_netflex = [
            plant
            for consumer in model.Consumer_NETFLEX
            for plant in Map_consumer_plant[consumer]  # type: ignore
            if Map_plant_tech[plant] == "v2g"
            or Map_plant_tech[plant] == "v1g"
            or Map_plant_tech[plant] == "bt"
        ] + Plant_list_rep_bat

        fix_variables(model.gen_max, Plant_list_EV_BT_netflex, gen_max_EV_BT_data)
        fix_variables(model.pmp_max, Plant_list_EV_BT_netflex, pmp_max_EV_BT_data)
        fix_variables(
            model.gen_energy_max,
            Plant_list_EV_BT_netflex,
            gen_energy_max_EV_BT_data,
        )
        print("time to fix values of EVs and batteries: ", time.time() - start)

    # fix generation capacity of plants from TYNDP dataset ----------
    start = time.time()
    tech_to_fix_gen_capacity = "all"
    # find target_techs that are technologies whose generation capacity is to be fixed
    # target_techs in current version. ['psp_close', 'battery', 'limited_energy', 'dam', 'lignite', 'psp_open', 'hardcoal', 'oil', 'nuclear', 'chp', 'dsr', 'gas']
    model_techs_list = [element for element in model.Tech_gen]
    target_techs = [
        element for element in model_techs_list if element not in ["pvrf", "windon", "windof", "v1g", "v2g", "bt", "hp"]
    ]
    
    if tech_to_fix_gen_capacity == "all":
        # fixing generation capacity of plants
        Plant_list_to_fix = [
            plant for plant in model.P if Map_plant_tech[plant] in target_techs
        ]  # type: ignore
        fix_variables(model.gen_max, Plant_list_to_fix, Plant_capacity_gen)

        # fixing pumping capacity of hyrdo plants (e.g., not batteries)
        Plant_list_to_fix = [
            plant for plant in model.P_hydro if Map_plant_tech[plant] != "dam"
        ]  # type: ignore
        fix_variables(model.pmp_max, Plant_list_to_fix, Plant_capacity_pmp)

        # fixing pumping capacity of batteries to their generation capacity (gen_max= pmp_max)
        Plant_list_to_fix = [
            plant for plant in model.P_pumping if Map_plant_tech[plant] == "battery"
        ]  # type: ignore
        fix_variables(model.pmp_max, Plant_list_to_fix, Plant_capacity_gen)

        # fixing energy capacity of hydro plants (e.g., not batteries)
        Plant_list_to_fix = [plant for plant in model.P_hydro]  # type: ignore
        fix_variables(model.gen_energy_max, Plant_list_to_fix, Plant_capacity_strg)

        # fixing energy capacity of batteries
        Plant_list_to_fix = [
            plant for plant in model.P_pumping if Map_plant_tech[plant] == "battery"
        ]  # type: ignore
        battery_storage_power_ratio = (
            6  # number of hours of storage if charging at full power
        )
        Plant_capacity_strg_battery = {
            plant: battery_storage_power_ratio * Plant_capacity_gen[plant]
            for plant in Plant_list_to_fix
        }
        fix_variables(
            model.gen_energy_max, Plant_list_to_fix, Plant_capacity_strg_battery
        )

    print("time to fix generation capacity of plants: ", time.time() - start)
    # %%     ------------------------------------------------------------------------------------------
    # create output folder, if it does not exist. Needs to be created before solve, because the log file is created in the output folder
    if not os.path.exists("output\\" + scenario_name + "\\"):
        os.makedirs("output\\" + scenario_name + "\\")

    print("Solving the model ...")
    solve_timer_start = time.time()
    opt = SolverFactory(settings_scen["solver_name"])

    # Specify the desired path for the log file
    opt.options["LogFile"] = "output//" + scenario_name + "//solver_log.log"

    # so that dual values are reported back from the solve
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    solver_parameters = (
        # Method=1 SimplexPricing=2 Presolve=1 ScaleFlag=1
        "ResultFile=model.ilp ScaleFlag=1"
    )

    # tee: prints solver statements (summary)
    result = opt.solve(
        model,
        tee=True,
        keepfiles=False,
        options_string=solver_parameters,
        symbolic_solver_labels=True,
    )
    solve_time = time.time() - solve_timer_start
    print("time to solve the model: ", solve_time)

    # %% export statistics
    termination_condition = str(result.solver.termination_condition)
    solve_status = str(result.solver.status)
    obj_value = pyo.value(model.OBJ)
    num_vars = len(list(model.component_data_objects(pyo.Var, active=True)))
    num_constraints = len(
        list(model.component_data_objects(pyo.Constraint, active=True))
    )

    # Creating a dictionary to hold the variables
    data = {
        "Variable": [
            "Termination_Condition",
            "Solver_Status",
            "Objective_Value",
            "solve_time",
            "NO_Variables",
            "NO_Constraints",
        ],
        "Value": [
            termination_condition,
            solve_status,
            obj_value,
            solve_time,
            num_vars,
            num_constraints,
        ],
    }

    # Creating a DataFrame from the dictionary
    df = pd.DataFrame(data)

    # Exporting the DataFrame to a CSV file
    df.to_csv("output//" + scenario_name + "//statistics.csv", index=False)
    # %% export result ----------------------------------------------------------------------------------
    print("Exporting the results ...")
    # Variables ----------------------------------------------------
    var_list = [
        v for v in model.component_objects(ctype=Var, active=True, descend_into=True)
    ]

    res_export.par_var(var_list, scenario_name)

    # Parameters ---------------------------------------------------
    par_list = [
        v for v in model.component_objects(ctype=Param, active=True, descend_into=True)
    ]

    res_export.par_var(par_list, scenario_name)
    # Sets ---------------------------------------------------------
    # set_list = [
    #     v for v in model.component_objects(ctype=Set, active=True, descend_into=True)
    # ]
    # for set_obj in set_list:
    #     set_name = set_obj.name
    #     print(set_name)
    #     if not set_name.endswith("index"):
    #         element_dict = {}
    #         counter = 0
    #         for element in set_obj:
    #             element_dict[counter] = [element]
    #             counter += 1
    #         dimension = len(element_dict[0])
    #         df = pd.DataFrame(element_dict.values(),  columns=[
    #             "Dimension_"+str(i) for i in range(dimension)])
    #         df.to_csv(f"output\\{scenario_name}\\{set_name}.csv", index=False)

    # Dual values ------------------------------------------------
    # exports all dual values of constraints automatically in seperate files named after variable's name

    constraint_names_to_export = [
        "energy_balance",
        "storage_soc",
        "storage_soc_limit",
        "lineATClimit",
    ]

    constraint_list = [
        v
        for v in model.component_objects(
            ctype=Constraint, active=True, descend_into=True
        )
        if v.name in constraint_names_to_export
    ]

    res_export.constraints(constraint_list, scenario_name, model)

    # emtying lists and dicts before next run -----------------------------------------------------------
    list_of_lists_netflex, list_of_dicts_netflex = get_lists_and_dicts(
        data_prep.definitions_NETFLEX, []
    )
    list_of_lists_common, list_of_dicts_common = get_lists_and_dicts(
        data_prep.definitions_common, []
    )
    list_of_lists_tyndp, list_of_dicts_tyndp = get_lists_and_dicts(
        data_prep.definitions_TYNDP, []
    )
    for list_name in list_of_lists_netflex + list_of_lists_common + list_of_lists_tyndp:
        try:
            exec(f"{list_name}.clear()")
        except AttributeError:
            print(list_name + " was possibly empty")

    for dict_name in list_of_dicts_netflex + list_of_dicts_common + list_of_dicts_tyndp:
        exec(f"{dict_name}.clear()")
