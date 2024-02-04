import pandas as pd
import os


def import_gen_demand_timeseries(output_dir):
    # TODO: change all instances of 8230 to the correct number based on "consumers_representing" in scenarios.py First, consumers_representing should be exported to the output folder (possibly in statistics.csv)
    print("Importing data from csvs...")
    time_indices = pd.read_csv(output_dir + "gen.csv").loc[:, "T"].unique().tolist()  # type: ignore

    # generation ------------------------------------------
     # generations per plant and time steps
    generation_all = (
        pd.read_csv(output_dir + "gen.csv")
        .pivot(index="P_gen", columns="T", values="value")
        .reindex(columns=time_indices)
    ) 

    for consumer_id in range(1, 300+1):
        file_path = output_dir + "ID" + str(consumer_id) + "_gen.csv"
        # if file file_path exists, read it and append it to generation_all
        if os.path.isfile(file_path):
            data_consumer = pd.read_csv(file_path, header=0, names=["P_gen", "T", "value"])
            generation_all_consumer = 8230 * data_consumer.pivot(index="P_gen", columns="T", values="value").reindex(columns=time_indices)
            generation_all = pd.concat([generation_all,generation_all_consumer])

    # demand inflexible ------------------------------------------  
    # flexible demand per consumer and time steps
    demand_inflx_all = (
        pd.read_csv(output_dir + "demand.csv")
        .pivot(
            index=["Consumer", "Consumption_types_inflex"], columns="T", values="value"
        )
        .reindex(columns=time_indices)
    )  

    for consumer_id in range(1, 300+1):
        file_path = output_dir + "ID" + str(consumer_id) + "_demand.csv"
        # if file file_path exists, read it and append it to demand_inflx_all
        if os.path.isfile(file_path):
            data_consumer = pd.read_csv(file_path, header=0, names=["Consumer", "Consumption_types_inflex", "T", "value"])
            demand_inflx_all_consumer =  8230 *  data_consumer.pivot(index=["Consumer", "Consumption_types_inflex"], columns="T", values="value").reindex(columns=time_indices)
            demand_inflx_all = pd.concat([demand_inflx_all,demand_inflx_all_consumer])

    # demand flexible ------------------------------------------
    # inflexible demand, including consumers', battery storage, PSP, per plant and time steps
    demand_flxbl_all = (
        pd.read_csv(output_dir + "storage_charge.csv")
        .pivot(index="P_pumping", columns="T", values="value")
        .reindex(columns=time_indices)
    )  
    
    for consumer_id in range(1, 300+1):
        file_path = output_dir + "ID" + str(consumer_id) + "_storage_charge.csv"
        # if file file_path exists, read it and append it to demand_flxbl_all
        if os.path.isfile(file_path):
            data_consumer = pd.read_csv(file_path, header=0, names=["P_pumping", "T", "value"])
            demand_flxbl_all_consumer =  8230 *  data_consumer.pivot(index="P_pumping", columns="T", values="value").reindex(columns=time_indices)
            demand_flxbl_all = pd.concat([demand_flxbl_all,demand_flxbl_all_consumer])

    # prices ------------------------------------------
    # prices, per node and time steps
    price_all = (
        pd.read_csv(output_dir + "energy_balance_dual.csv")
        .pivot(index="Node", columns="T", values="value")
        .reindex(columns=time_indices)
    )  

    # soc dual ------------------------------------------
    # marginal value of storage (opportunity cost), per storage plant and time steps
    soc_dual_all = (
        pd.read_csv(output_dir + "storage_soc_dual.csv")
        .pivot(index="P_storage", columns="T", values="value")
        .reindex(columns=time_indices)
    )  

    # export ------------------------------------------
    # trade over lines, per line and time steps
    # negative value indicates trade to start_node from end_node in Map_line_node
    export_all = (
        pd.read_csv(output_dir + "Export.csv")
        .pivot(index="lineATC", columns="T", values="value")
        .reindex(columns=time_indices)
    )  

    # soc -----------------------------------------------  
    # state of charge
    soc_all = (
        pd.read_csv(output_dir + "soc.csv")
        .pivot(index="P_storage", columns="T", values="value")
        .reindex(columns=time_indices)
    )  

    # lost load ------------------------------------------
    # lost load, per consumer and time steps
    lostload_all = (
        pd.read_csv(output_dir + "lostload.csv")
        .pivot(index="Consumer", columns="T", values="value")
        .reindex(columns=time_indices)
    )

    return (
        generation_all,
        demand_inflx_all,
        demand_flxbl_all,
        export_all,
        soc_all,
        price_all,
        soc_dual_all,
    )
