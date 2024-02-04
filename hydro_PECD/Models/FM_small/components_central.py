from pyomo.environ import *
from components_common import intersection


def define_constraints_central(
    model,
    consumer_based_on_tariff,
    winter_limit,
):
    # if consumers ARE based on tariff, their consumption is already planned, no need to model here.
    if not consumer_based_on_tariff:
        for p, data in model.Data_plant_flex_d_within_window.items():
            for i, time_range in enumerate(data["time_horizon"]):
                n = i + 1
                start, end = time_range
                if "t_" + str(start) in model.T and "t_" + str(end) in model.T:
                    # TODO above what if only one of the t_start and t_end is in model.T?
                    # Initialize energy_limit with a default value
                    energy_limit = data["energy"][i]
                    model.add_component(
                        f"consume_tot_limit_{p}_{n}",
                        Constraint(
                            expr=sum(
                                model.storage_charge[p, "t_" + str(t)]
                                for t in range(start, end + 1)
                            )
                            == energy_limit
                        ),
                    )
    if winter_limit["mode"]:
        # limit the sum of import to CH00 in the given time window winter_limit["window"] to the given value winter_limit["energy_MWh"]
        n="CH00"

        t_start = winter_limit["window"][0] 
        t_end = winter_limit["window"][1]
        if t_start > t_end:
            T_winter_list = ["t_" + str(t) for t in range(t_start, 8760 + 1)] + [
                "t_" + str(t) for t in range(1, t_end + 1)
            ]  
        else:
            T_winter_list = ["t_" + str(t) for t in range(t_start, t_end + 1)]  

        model.T_winter = Set(within=model.T, initialize=T_winter_list)

        export_as_starting_node = sum(
            model.Export[l, t] for l in model.lineATC & model.Map_node_exportinglineATC[n] for t in model.T_winter
        )   
        # positive means import, negative means export
        import_as_ending_node = sum(
            model.Export[l, t] for l in model.lineATC & model.Map_node_importinglineATC[n] for t in model.T_winter
        )

        model.Constraint_winter_limit = Constraint(
            expr=import_as_ending_node - export_as_starting_node <= winter_limit["energy_MWh"]
        )




