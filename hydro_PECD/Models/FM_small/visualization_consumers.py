import pandas as pd
import plotly.graph_objects as go
import os.path
from scenarios.scenarios import scenarios_list

# identify scenarios that have consumers based on tariff
scenarios_with_tariff = [
    scenario
    for scenario in scenarios_list
    if scenarios_list[scenario]["consumer_based_on_tariff"] == True
]

scenarios_to_plot = scenarios_with_tariff

consumers_list = ["ID" + str(i) for i in range(199, 199 + 2)]
variables_to_be_plotted = [
    "demand",
    "storage_charge",
    "gen",
    "exported",
    "imported",
    "tariff_import",
    "tariff_export",
    "infeed",
    "lostload",
    "curtailment",
]


def plot_time_series(file_name_dict):
    """
    Plot time series for each consumer and each variable
    """
    for var in variables_to_be_plotted:
        # if file file_name_dict[consumer][var] does not exist, skip
        if os.path.isfile(file_name_dict[consumer][var]):
            df = pd.read_csv(file_name_dict[consumer][var], index_col=False)
        else:
            print(file_name_dict[consumer][var] + " does not exist")
            continue

        # find uniqe elements in first column, and for each unique element plot the corresponding time series
        for plant in df.iloc[:, 0].unique():
            df_plant = df[df.iloc[:, 0] == plant]
            if var == "tariff_import":
                fig.add_trace(go.Scatter(x=df_plant.iloc[:, 1], y=df_plant.iloc[:, 2] / 60, name=var + "_" + plant))  # type: ignore
            else:
                fig.add_trace(go.Scatter(x=df_plant.iloc[:, 1], y=df_plant.iloc[:, 2], name=var + "_" + plant))  # type: ignore


def file_name_dict_init():
    """
    Create a dictionary with the file names for each consumer and each variable.
    This directly depends on how data are exported in the simulation.
    Output: file_name_dict[consumer][var] = "output\\" + scenario + "\\" + consumer + "_" + var + ".csv"
    e.g file_name_dict {'ID290': {'gen': 'output\\s0001\\ID290_gen.csv', 'exported': 'output\\s0001\\ID290_exported.csv',
    """
    file_name_dict = {}
    for consumer in consumers_list:
        file_name_dict[consumer] = {}
        for var in variables_to_be_plotted:
            file_name_dict[consumer][var] = (
                "output\\" + scenario + "\\" + consumer + "_" + var + ".csv"
            )
    return file_name_dict


for scenario in scenarios_to_plot:
    file_name_dict = (
        file_name_dict_init()
    )  # create a dictionary with the file names for each consumer and each variable
    for consumer in consumers_list:
        fig = go.Figure()  # type: ignore
        plot_time_series(file_name_dict)  # add traces to the figure
        fig.update_layout(
            title=scenario + "_" + consumer,
            xaxis_title="time",
            yaxis_title="power [MW]",
        )
        # limit x-axis to first 168 hours
        fig.update_xaxes(range=[169, 2 * 168])  # Zoom on 2nd week
        fig.show()
