from scenarios.settings_default import seetings_default_param
from scenarios.scenarios import scenarios_list


def read_scenario_settings(scenario_name):
    # Use default parameters if a parameters as stored in seetings_default_param, if it  is missing in the scenarios_list
    parameters = scenarios_list.get(scenario_name, {})
    scenario_params = {**seetings_default_param, **parameters}

    # bools are immutable, don't need copying
    consumer_based_on_tariff = scenario_params["consumer_based_on_tariff"]
    consumer_connection_limit = scenario_params["consumer_connection_limit"]
    flex_dem_active_for_consumer = scenario_params["flex_dem_active_for_consumer"]

    # strings are immutable, don't need copying
    solver_name = scenario_params["solver_name"]
    t_start = scenario_params["t_start"]
    t_end = scenario_params["t_end"]
    weather_year = scenario_params["weather_year"]
    run_year = scenario_params["run_year"]
    eu_policy = scenario_params["eu_policy"]
    ch_policy = scenario_params["ch_policy"]
    consumer_start = scenario_params["consumer_start"]
    consumer_end = scenario_params["consumer_end"]
    opt_mode = scenario_params["opt_mode"]

    Node_list = scenario_params["Node_list"].copy()
    consumers_representing = scenario_params["consumers_representing"]
    slack_soc = scenario_params["slack_soc"]
    single_large_battery = scenario_params["single_large_battery"]

    winter_limit = scenario_params["winter_limit"]
    rep_hydro_plants = scenario_params["rep_hydro_plants"]
    res_investment_allowed = scenario_params["res_investment_allowed"]

    NTC_CH_ratio = scenario_params["NTC_CH_ratio"]

    # list of consumers that are included in the model
    Consumer_list_netflex = [
        "ID" + str(i) for i in range(consumer_start, consumer_end + 1)
    ]
    if t_start > t_end:
        T_list = ["t_" + str(t) for t in range(t_start, 8760 + 1)] + [
            "t_" + str(t) for t in range(1, t_end + 1)
        ]  # time steps
    else:
        T_list = ["t_" + str(t) for t in range(t_start, t_end + 1)]  # time steps
    # return all of variables in one short format, possibly a dictionary
    return {
        "consumer_based_on_tariff": consumer_based_on_tariff,
        "consumer_connection_limit": consumer_connection_limit,
        "solver_name": solver_name,
        "flex_dem_active_for_consumer": flex_dem_active_for_consumer,
        "t_start": t_start,
        "t_end": t_end,
        "Node_list": Node_list,
        "weather_year": weather_year,
        "run_year": run_year,
        "eu_policy": eu_policy,
        "ch_policy": ch_policy,
        "consumer_start": consumer_start,
        "consumer_end": consumer_end,
        "opt_mode": opt_mode,
        "Consumer_list_netflex": Consumer_list_netflex,
        "T_list": T_list,
        "consumers_representing": consumers_representing,
        "slack_soc": slack_soc,
        "single_large_battery": single_large_battery,
        "winter_limit": winter_limit,
        "rep_hydro_plants": rep_hydro_plants,
        "res_investment_allowed": res_investment_allowed,
        "NTC_CH_ratio": NTC_CH_ratio,
    }


# scenario_name = "scenario_1"
# settings_scen = read_scenario_settings(scenario_name)
