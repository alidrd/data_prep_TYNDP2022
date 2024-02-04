# from read_settings import consumer_connection_limit, solver_name, flex_dem_active_for_consumer, consumer_based_on_tariff  # type: ignore

from pydoc import doc
from read_settings import read_scenario_settings
import pyomo.environ as pyo

# from pyomo.opt import ProblemFormat
from pyomo.environ import (
    ConcreteModel,
    Objective,
    Constraint,
    Var,
    SolverFactory,
    maximize,
)
import pandas as pd
from data_prep.data_import_NETFLEX import data_import_NETFLEX_fcn
from components_common import (
    define_sets,
    define_params_op,
    define_vars_op,
    define_vars_inv,
    define_constraints,
    consumer_import_Constraint,
    consumer_export_Constraint,
    fix_variables,
)
from components_consumer_opt import (
    obj_expression_consumer,
    energy_balance_Constraint_consumer,
    define_params_consumer,
    define_sets_vars_params_consumer_utility_max,
    define_constraints_consumer,
)

from utils.utilities_model import export_model_to_txt
from structural_parameters import tech_infeed_consumers_list
from structural_parameters import (
    tech_demand_with_timeseries_netflex_model_list,
    tech_infeed_consumers_list,
    tech_demand_assets_shiftable_netflex_list,
    Start_condition_tech,
    # tech_inflex_demand_in_flex_dem_active_for_consumer,
    tariff_export_definitions,
    tariff_import_definitions,
)

from data_import_fcns import map_tech_to_plant
from data_prep.definitions_common import *
from data_prep.definitions_NETFLEX import *
import time
import os
from data_import_fcns import tou_tariff


def consumers_opt_fcn(scenario_name):
    """
    This function optimizes the consumers' cost minization (or utility maximization) problem.  
    Given the assets and tariff faced by each consumer, the optimization problem determines the optimal dispatch of the consumer's assets, including EVs, batteries, heatpumps, and PVs.
    Inputs:
        scenario_name: name of the scenario to be optimized
    Outputs:
        exported_all_consumers: dictionary with the exported energy of all consumers
        imported_all_consumers: dictionary with the imported energy of all consumers
        flex_demand_in_durations: dictionary with the flex demand in durations of all consumers
        Results of the optimization are exported to csv files in the output folder.
    """
    settings_scen = read_scenario_settings(scenario_name)
    consumer_based_on_tariff = settings_scen["consumer_based_on_tariff"]
    consumer_connection_limit = settings_scen["consumer_connection_limit"]

    if consumer_based_on_tariff:
        # read settings ----------------------------------------------------------------------------
        T_list = settings_scen["T_list"]
        Consumer_list_netflex = settings_scen["Consumer_list_netflex"]
        flex_dem_active_for_consumer = settings_scen["flex_dem_active_for_consumer"]

        # Assign tariffs to consumers ---------------------------------------------------------------
        tariff_export_hourly = tou_tariff(
            tariff_export_definitions, "tariff_AEW", Consumer_list_netflex, T_list
        )
        tariff_import_hourly = tou_tariff(
            tariff_import_definitions, "tariff_AEW", Consumer_list_netflex, T_list
        )

        # defining which assets of the consumers are inflexible to be defined in the model.Demand_inflex_assets
        if flex_dem_active_for_consumer:
            tech_demand_inflex_selected = [
                "fixed",
            ]
        else:
            # making all assets inflexible
            tech_demand_inflex_selected = tech_demand_assets_shiftable_netflex_list + [
                "fixed"
            ]

        # run individual optimization for each consumer ---------------------------------------------
        for consumer in Consumer_list_netflex:
            print("Optimizing for consumer: " + consumer + 50 * "-")
            start = time.time()
            
            # create a new model for every consumer
            model = ConcreteModel() 

            # plants_active is all plants except "pv" (tech_infeed_consumers_list)
            plants_active = [
                plant
                for plant in Map_consumer_plant[consumer]
                if Map_plant_tech[plant] not in tech_infeed_consumers_list
            ]

            # tech_demand_time_series are demand asset types that have time series in the dataset ["fixed", "hp", "v1g", "v2g"]
            tech_demand_time_series = tech_demand_with_timeseries_netflex_model_list


            # defne sets, parameters, variables, constraints -----------------------------------------
            # NOTE: [consumer] probably does not work for multiple consumers. NOTE: some variables are defined too broadly, e.g. Node_list considers all countries, not just consumers'
            define_sets(
                model,
                plants_active,
                [consumer],
                [consumer],
                tech_infeed_consumers_list,
                T_list,
                [
                    "CH00",
                ],
                Consumer_list_netflex,
                tech_demand_time_series,
                tech_demand_inflex_selected,
            )  # NOTE: adjust ["CH00",] where more nodes in CH

            define_params_consumer(
                model,
                tariff_import_hourly,
                tariff_export_hourly,
                Consumer_import_max,
                Consumer_export_max,
                Map_consumer_optimization[consumer],
                Map_consumer_plant[consumer],
            )

            define_params_op(model)
            define_vars_op(model)
            define_vars_inv(model)
            define_sets_vars_params_consumer_utility_max(model)

            # Objective function ------------------------------------------------------------------------------------------------------------------
            model.OBJ = Objective(rule=obj_expression_consumer, sense=maximize)

            # consumer connection limits -----------------------------------------------------------------------------------------------------------
            if consumer_connection_limit:
                model.consumer_import_limit = Constraint(
                    model.Consumer, model.T, rule=consumer_import_Constraint
                )  

                model.consumer_export_limit = Constraint(
                    model.Consumer, model.T, rule=consumer_export_Constraint
                )

            # Constraints -------------------------------------------------------------------------------------------------------------------------
            # export_model_to_txt(consumer, model)
            define_constraints(model)
            define_constraints_consumer(model)
            # energy balance for consumer
            model.energy_balance = Constraint(
                model.Consumer, model.T, rule=energy_balance_Constraint_consumer
            )

            # fixing values ------------------------------------------------------------------------------------------------------------------------
            # fix values of EVs
            Plant_list_EVs_netflex = [
                plant
                for plant in Map_consumer_plant[consumer]
                if Map_plant_tech[plant] == "v2g"
                or Map_plant_tech[plant] == "v1g"
            ]

            fix_variables(
                model.gen_max, Plant_list_EVs_netflex, gen_max_EV_BT_data_netflex
            )

            fix_variables(
                model.pmp_max, Plant_list_EVs_netflex, pmp_max_EV_BT_data_netflex
            )

            fix_variables(
                model.gen_energy_max,
                Plant_list_EVs_netflex,
                gen_energy_max_EV_BT_data_netflex,
            )

            # fix values of batteries
            Plant_list_batteries_netflex = [
                plant
                for plant in Map_consumer_plant[consumer]
                if Map_plant_tech[plant] == "bt"
            ]

            fix_variables(
                model.gen_max, Plant_list_batteries_netflex, gen_max_EV_BT_data_netflex
            )

            fix_variables(
                model.pmp_max, Plant_list_batteries_netflex, pmp_max_EV_BT_data_netflex
            )

            fix_variables(
                model.gen_energy_max,
                Plant_list_batteries_netflex,
                gen_energy_max_EV_BT_data_netflex,
            )

            print("Build time: " + str(time.time() - start) + " seconds...")

            # Solve --------------------------------------------------------------------------------------------------------------------------------
            # # so that dual values are reported back from the solve
            # model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
            # solver name
            # model.write(filename="model" + consumer + ".mps", format=ProblemFormat.mps)
            opt = SolverFactory(settings_scen["solver_name"])
            # Set solver options
            # opt.options["method"] = 0
            # opt.options["prepasses"] = 1
            # opt.options["presolve"] = 1
            # # tee: prints solver statements (summary)
            results = opt.solve(model)  # , tee=True
            # # store results in results object
            # model.solutions.store_to(results)
            print("Solver status: ", results.solver.status)
            print(
                "Solver termination condition: ", results.solver.termination_condition
            )
            # print("Objective value: ", model.OBJ())  # type: ignore
            # export_model_to_txt(consumer, model)                  # write the model to a txt file
            print("Build + solve time: " + str(time.time() - start) + " seconds...")
            # %% export result ----------------------------------------------------------------------------------------------------------------------
            imported_all_consumers[consumer] = model.imported
            exported_all_consumers[consumer] = model.exported
            flex_demand_in_durations[consumer] = model.flex_demand_in_durations

            # export results to csv files ----------------------------------------------------------------------------------------------------------
            # objective value ---------------------------------
            if not os.path.exists("output\\" + scenario_name + "\\"):
                os.makedirs("output\\" + scenario_name + "\\")
            # save the optimal value of the objective function into a csv file
            with open(
                "output\\" + scenario_name + "\\" + consumer + "_" + "obj_value.csv",
                "w",
            ) as f:
                f.write(str(pyo.value(model.OBJ)))

            # Variables ---------------------------------------
            print("Exporting variables and selected parameters ...")
            # exports all variables automatically in seperate files named after variable's name
            # if only a sublist is needed, adjust var_list
            var_list = [
                v
                for v in model.component_objects(
                    ctype=Var, active=True, descend_into=True
                )
            ]
            # add model.demand, model.tariff_import, model.tariff_export to var_list
            parameters_to_export = [
                "demand",
                "tariff_import",
                "tariff_export",
                "infeed",
            ]
            for parameter in parameters_to_export:
                var_list.append(getattr(model, parameter))

            for variable in var_list:
                # print("Exporting " + variable.name + " ...")
                # create folder "output\\" + scenario + "\\" if does not exist
                extracted_info = variable.extract_values()
                result_values = pd.DataFrame(
                    index=extracted_info.keys(), data=extracted_info.values()
                )
                if not result_values.empty:
                    result_values.to_csv(
                        "output\\"
                        + scenario_name
                        + "\\"
                        + consumer
                        + "_"
                        + variable.name
                        + ".csv"
                    )
                # result_values.to_csv("output\\" + variable.name + ".csv")
            print(
                "Build + solve + export to csv time: "
                + str(time.time() - start)
                + " seconds."
            )
