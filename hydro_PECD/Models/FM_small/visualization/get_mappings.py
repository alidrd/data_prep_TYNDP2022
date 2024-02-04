import pandas as pd


def get_mappings(output_dir):
    # Initialize the output dictionaries
    Map_node_plant = {}
    Map_node_consumer = {}
    Map_node_exportinglineATC = {}
    Map_node_importinglineATC = {}
    Map_plant_tech = {}

    # Load data from CSV files and create dictionaries
    Map_node_plant = pd.read_csv(
        output_dir + "Map_node_plant.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_node_plant = {
        key: [x for x in value if str(x) != "nan"]
        for key, value in Map_node_plant.items()
    }

    Map_node_consumer = pd.read_csv(
        output_dir + "Map_node_consumer.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_node_consumer = {
        key: [x for x in value if str(x) != "nan"]
        for key, value in Map_node_consumer.items()
    }

    Map_node_exportinglineATC = pd.read_csv(
        output_dir + "Map_node_exportinglineATC.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_node_exportinglineATC = {
        key: [x for x in value if str(x) != "nan"]
        for key, value in Map_node_exportinglineATC.items()
    }

    Map_node_importinglineATC = pd.read_csv(
        output_dir + "Map_node_importinglineATC.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_node_importinglineATC = {
        key: [x for x in value if str(x) != "nan"]
        for key, value in Map_node_importinglineATC.items()
    }

    Map_plant_tech = pd.read_csv(
        output_dir + "Map_plant_tech.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_plant_tech_consumers = pd.read_csv(
         "visualization/Map_plant_tech_consumers.csv", index_col=0, header=0
    ).T.to_dict("list")

    Map_plant_tech.update(Map_plant_tech_consumers)

    return (
        Map_node_plant,
        Map_node_consumer,
        Map_node_exportinglineATC,
        Map_node_importinglineATC,
        Map_plant_tech,
    )
