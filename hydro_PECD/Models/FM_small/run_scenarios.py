from scenarios.scenarios import scenarios_list
from core import core_main

for scenario_name, parameters in scenarios_list.items():
    print(70 * "-")
    print(f"Running scenario: {scenario_name}")
    print(70 * "-")
    core_main(scenario_name)
