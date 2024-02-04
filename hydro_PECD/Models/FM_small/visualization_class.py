import plotly.graph_objects as go
import pandas as pd
from visualization.get_mappings import get_mappings
from visualization.import_gen_dem_ts import import_gen_demand_timeseries
from visualization.map_ts import map_gen_dem_timeseries
import os


class DemandTimeSeriesPlotter:
    def __init__(self, target_node):
        self.output_dir = ""
        self.scenario_name = ""
        self.target_node = target_node
        self.generation_all = pd.DataFrame()
        self.demand_inflx_all = pd.DataFrame()
        self.demand_flxbl_all = pd.DataFrame()
        self.export_all = pd.DataFrame()
        self.soc_all = pd.DataFrame()
        self.sum_assets = True
        self.fig_price = go.Figure()
        self.fig_sum_gen = go.Figure()
        self.fig_ind_gen = go.Figure()
        self.fig_agg_gen = go.Figure()
        self.fig_sum_dem = go.Figure()
        self.fig_agg_dem = go.Figure()
        self.fig_ind_dem = go.Figure()
        self.fig_export_import = go.Figure()
        self.fig_soc = go.Figure()

    # NOTE: add a graph for state of charge. possibly copy the code from visualization.py

    def load_data(self):
        # Assuming you have functions to load the data, update the instance variables here
        (
            self.generation_all,
            self.demand_inflx_all,
            self.demand_flxbl_all,
            self.export_all,
            self.soc_all,
            self.price_all,
            self.soc_dual_all,
        ) = import_gen_demand_timeseries(self.output_dir)

        (
            Map_node_plant,
            Map_node_consumer,
            Map_node_exportinglineATC,
            Map_node_importinglineATC,
            self.Map_plant_tech,
        ) = get_mappings(self.output_dir)

        (
            self.plant_list,
            self.demand_inflx_list,
            self.demand_flxbl_list,
            self.exportATC_list,
            self.importATC_list,
            plant_with_soc,
        ) = map_gen_dem_timeseries(
            self.target_node,
            self.generation_all,
            self.demand_inflx_all,
            self.demand_flxbl_all,
            self.export_all,
            self.soc_all,
            Map_node_plant,
            Map_node_consumer,
            Map_node_exportinglineATC,
            Map_node_importinglineATC,
        )

    def plot_sum_gen(self, mode):
        self.fig_sum_gen.add_trace(
            go.Scatter(
                x=self.generation_all.sum(axis=0).index,
                y=self.generation_all.sum(axis=0),
                mode=mode,
                name=f"{self.scenario_name}_generation",
            )
        )

    def plot_ind_gen(self, mode):
        for plant in self.plant_list:
            self.fig_ind_gen.add_trace(
                go.Scatter(
                    x=self.generation_all.loc[plant, :].index,
                    y=self.generation_all.loc[plant, :],
                    mode=mode,
                    name=plant,
                )
            )

    def plot_agg_gen(self, mode):
        aggregated_data = {}
        for plant in self.plant_list:
            tech = tuple(self.Map_plant_tech.get(plant, []))  # Convert list to tuple
            if tech:
                if tech in aggregated_data:
                    aggregated_data[tech] = aggregated_data[tech].add(
                        self.generation_all.loc[plant, :], fill_value=0
                    )
                else:
                    aggregated_data[tech] = self.generation_all.loc[plant, :]

        for tech, data in aggregated_data.items():
            self.fig_agg_gen.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data,
                    mode=mode,
                    name=f"{self.scenario_name}_{tech[0]}",
                )
            )

    def plot_sum_dem(self, mode):
        self.fig_sum_dem.add_trace(
            go.Scatter(
                x=self.demand_inflx_all.sum(axis=0).index,
                y=self.demand_inflx_all.sum(axis=0),
                mode=mode,
                name=f"{self.scenario_name}_inflexible",
            )
        )
        self.fig_sum_dem.add_trace(
            go.Scatter(
                x=self.demand_flxbl_all.sum(axis=0).index,
                y=self.demand_flxbl_all.sum(axis=0),
                mode=mode,
                name=f"{self.scenario_name}_flexible",
            )
        )

        self.fig_sum_dem.add_trace(
            go.Scatter(
                x=self.demand_inflx_all.sum(axis=0).index,
                y=self.demand_inflx_all.sum(axis=0) + self.demand_flxbl_all.sum(axis=0),
                mode=mode,
                name=f"{self.scenario_name}_total",
            )
        )

    def plot_ind_dem(self, mode):
        # Plot flexible demand individually
        for demand_name in self.demand_flxbl_list:
            self.fig_ind_dem.add_trace(
                go.Scatter(
                    x=self.demand_flxbl_all.loc[demand_name, :].index,
                    y=self.demand_flxbl_all.loc[demand_name, :],
                    mode=mode,
                    name=demand_name,
                )
            )

        # Plot inflexible demand
        for demand_name in self.demand_inflx_list:
            self.fig_ind_dem.add_trace(
                go.Scatter(
                    x=self.demand_inflx_all.loc[demand_name, :].index,
                    y=self.demand_inflx_all.loc[demand_name, :],
                    mode=mode,
                    name=demand_name,
                )
            )

    def plot_agg_dem(self, mode):
        aggregated_data = {}
        for plant in self.demand_flxbl_list:
            # self.Map_plant_tech[plant] is a list with one element
            tech = self.Map_plant_tech[plant][0]
            if tech in aggregated_data:
                aggregated_data[tech] = aggregated_data[tech].add(
                    self.demand_flxbl_all.loc[plant, :], fill_value=0
                )
            else:
                aggregated_data[tech] = self.demand_flxbl_all.loc[plant, :]

        for tech, data in aggregated_data.items():
            self.fig_agg_dem.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data,
                    mode=mode,
                    name=f"{self.scenario_name}_{tech}",
                )
            )

    def plot_export_import(self, mode):
        for line in self.exportATC_list:
            self.fig_export_import.add_trace(
                go.Scatter(
                    x=self.export_all.loc[line, :].index,
                    y=-self.export_all.loc[line, :],
                    mode=mode,
                    name=f"{self.scenario_name}_Import_{line}",
                )
            )
        for line in self.importATC_list:
            self.fig_export_import.add_trace(
                go.Scatter(
                    x=self.export_all.loc[line, :].index,
                    y=self.export_all.loc[line, :],
                    mode=mode,
                    name=f"{self.scenario_name}_Export_{line}",
                )
            )

        # Plot export - all
        # export_sum is equal to sum of exports minus sum of imports,
        # that is sum of values for lines in exportATC_list minus sum of values for lines in importATC_list
        export_sum = (
            -self.export_all.loc[self.exportATC_list, :].sum()
            + self.export_all.loc[self.importATC_list, :].sum()
        )

        self.fig_export_import.add_trace(
            go.Scatter(
                x=export_sum.index,
                y=export_sum,
                mode=mode,
                name=f"{self.scenario_name}_Export_all",
            )
        )

    def plot_price(self, mode):
        for node in [
            self.target_node,
        ]:
            self.fig_price.add_trace(
                go.Scatter(
                    x=self.price_all.loc[node, :].index,
                    y=self.price_all.loc[node, :],
                    mode=mode,
                    name=f"{self.scenario_name}_{node}",
                )
            )

    def plot_soc(self, mode):
        # plants with soc are defined as plants that are in self.plant_list and self.soc_all.index
        plants_with_soc = [
            plant for plant in self.plant_list if plant in self.soc_all.index
        ]

        for plant in plants_with_soc:
            if plant in self.soc_all.index:
                self.fig_soc.add_trace(
                    go.Scatter(
                        x=self.soc_all.loc[plant, :].index,
                        y=self.soc_all.loc[plant, :],
                        mode=mode,
                        name=f"{self.scenario_name}_{plant}",
                    )
                )
        # add a trace that sums up the soc of all plants that are in self.plant_list and self.soc_all.index
        self.fig_soc.add_trace(
            go.Scatter(
                x=self.soc_all.loc[plants_with_soc, :].sum(axis=0).index,
                y=self.soc_all.loc[plants_with_soc, :].sum(axis=0),
                mode=mode,
                name=f"{self.scenario_name}_SOC_all",
            )
        )

    def plot_all(self, mode):
        print("Plotting price time series...")
        self.plot_price(mode)

        print("Plotting generation and demand time series...")
        fig = go.Figure()
        self.plot_sum_gen(mode)
        self.plot_sum_dem(mode)

        if not self.sum_assets:
            print("Plotting individual generation and demand time series...")
            self.plot_ind_dem(mode)
            self.plot_ind_gen(mode)
        else:
            print("Plotting aggregated generation and demand time series...")
            self.plot_agg_dem(mode)
            self.plot_agg_gen(mode)
        print("Plotting export and import time series...")
        self.plot_export_import(mode)
        self.plot_soc(mode)

    def show_all_plots(self, plot_range=[0, 168]):
        self.fig_price.update_xaxes(range=plot_range)
        self.fig_price.update_layout(title="Price")
        self.fig_price.show()

        self.fig_sum_gen.update_xaxes(range=plot_range)
        self.fig_sum_gen.update_layout(title="Generation")
        self.fig_sum_gen.show()

        self.fig_sum_dem.update_xaxes(range=plot_range)
        self.fig_sum_dem.update_layout(title="Demand")
        self.fig_sum_dem.show()

        if not self.sum_assets:
            self.fig_ind_gen.update_xaxes(range=plot_range)
            self.fig_ind_gen.update_layout(title="Individual generation")
            self.fig_ind_gen.show()

            self.fig_ind_dem.update_xaxes(range=plot_range)
            self.fig_ind_dem.update_layout(title="Individual demand")
            self.fig_ind_dem.show()

        else:
            self.fig_agg_gen.update_xaxes(range=plot_range)
            self.fig_agg_gen.update_layout(title="Aggregated generation")
            self.fig_agg_gen.show()

            self.fig_agg_dem.update_xaxes(range=plot_range)
            self.fig_agg_dem.update_layout(title="Aggregated demand")
            self.fig_agg_dem.show()

        self.fig_export_import.update_xaxes(range=plot_range)
        self.fig_export_import.update_layout(title="Export and import")
        self.fig_export_import.show()

        self.fig_soc.update_xaxes(range=plot_range)
        self.fig_soc.update_layout(title="State of charge")
        self.fig_soc.show()

    def export_all_plots_to_html(self, export_range=[0, 168]):  # 8760
        # if the folder plots do not exist, create it
        if not os.path.exists("plots"):
            os.makedirs("plots")
        self.fig_price.update_xaxes(range=export_range)
        self.fig_price.update_layout(title="Price")
        self.fig_price.write_html(f"plots/Price_{self.scenario_name}.html")

        self.fig_sum_gen.update_xaxes(range=export_range)
        self.fig_sum_gen.update_layout(title="Generation")
        self.fig_sum_gen.write_html(f"plots/Gen_{self.scenario_name}.html")

        self.fig_sum_dem.update_xaxes(range=export_range)
        self.fig_sum_dem.update_layout(title="Demand")
        self.fig_sum_dem.write_html(f"plots/Dem_{self.scenario_name}.html")

        if not self.sum_assets:
            self.fig_ind_gen.update_xaxes(range=export_range)
            self.fig_ind_gen.update_layout(title="Individual generation")
            self.fig_ind_gen.write_html(f"plots/Ind_gen_{self.scenario_name}.html")

            self.fig_ind_dem.update_xaxes(range=export_range)
            self.fig_ind_dem.update_layout(title="Individual demand")
            self.fig_ind_dem.write_html(f"plots/Ind_dem_{self.scenario_name}.html")

        else:
            self.fig_agg_gen.update_xaxes(range=export_range)
            self.fig_agg_gen.update_layout(title="Aggregated generation")
            self.fig_agg_gen.write_html(f"plots/Agg_gen_{self.scenario_name}.html")

            self.fig_agg_dem.update_xaxes(range=export_range)
            self.fig_agg_dem.update_layout(title="Aggregated demand")
            self.fig_agg_dem.write_html(f"plots/Agg_dem_{self.scenario_name}.html")

        self.fig_export_import.update_xaxes(range=export_range)
        self.fig_export_import.update_layout(title="Export and import")
        self.fig_export_import.write_html(f"plots/Exp_imp_{self.scenario_name}.html")

        self.fig_soc.update_xaxes(range=export_range)
        self.fig_soc.update_layout(title="State of charge")
        self.fig_soc.write_html(f"plots/SOC_{self.scenario_name}.html")

        print("All plots sucessfully exported...")


target_node = "CH00"  # a node name ("CH_00"), or "all"

scenarios_to_plot = [
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_T",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_T",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_higher_AF",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_higher_AF_T",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_higher_AF2",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_higher_AF4_T",
    # "scen_8230_uniform_cost_no_new_CH_RES_3rep_168_6_higher_AF4",
    "scenario_0001_2T_winter",
    # "scen_40_07_winter",
    # "scen_40_07_winter_T",
    # "scen_40_07_inv",
    # "scen_40_07_inv_T",
    # "scen_40_07_winter_inv",
    # "scen_40_07_winter_inv_T",
]


# output_dir = "output/" + scenario_name + "/"

plotter = DemandTimeSeriesPlotter(target_node)
for i_scenario in scenarios_to_plot:
    plotter.output_dir = "output/" + i_scenario + "/"
    plotter.scenario_name = i_scenario
    plotter.load_data()
    # plotter.plot_price(mode = "lines")
    plotter.plot_all(mode="lines")

plotter.show_all_plots()
plotter.export_all_plots_to_html()
