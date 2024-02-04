import aggregation.aggregate as agg
import os

# params and vars to aggregate across scenarios as keys, and the type of aggregation as values (sum, mean, min, max, or several of them)

params_vars_to_agg = {
    "statistics": {"type": "none", "temporal": False, "mappings": False},
    "gen_max": {"type": "sum", "temporal": False, "mappings": False},
    "gen_energy_max": {"type": "sum", "temporal": False, "mappings": False},
    "demand": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": ["temporal", "Map_node_consumer", "Map_type_consumer"],
    },
    "gen": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": ["temporal", "Map_node_plant"],
    },
    "energy_balance_dual": {
        "type": "mean",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": [
            "temporal",
        ],
    },
    "storage_charge": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": ["temporal", "Map_node_plant"],
    },
    "lostload": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": [
            "temporal",
        ],
    },
    "curtailment": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": [
            "temporal",
        ],
    },
    "infeed": {
        "type": "sum",
        "temporal": ["hour", "day", "week", "month", "season", "year"],
        "mappings": [
            "temporal",
        ],
    },
    "soc": {
        "type": "sum",
        "temporal": ["hour", "week"],
        "mappings": ["temporal", "Map_node_plant"],
    },
}

indicators_to_agg = {
    "price_weighted": [
        "mean",
    ],
}

scenarios_to_agg = [
    "scenario_0001_2T_winter",
]


agg_name = "0001_1000_7"
output_dir = "output/aggregated/" + agg_name + "/"

# update mappings based on the given scenarios
agg.mappings_merge(scenarios_to_agg, r"output/")


for item, agg_type in params_vars_to_agg.items():
    print("Aggregating " + item + 40 * "...")
    print(agg_type)
    agg.aggregate_params_vars(scenarios_to_agg, item, agg_type, output_dir)

for item, agg_type in indicators_to_agg.items():
    print("Aggregating " + item + 40 * "...")
    print(agg_type)
    agg.aggregate_indicators(scenarios_to_agg, item, agg_type, output_dir)

print("Aggregation complete.")
