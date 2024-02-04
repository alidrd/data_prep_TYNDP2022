from data_prep.definitions_common import (
    Demand_data,
    Demand_data_TYNDP,
    Infeed_RES_TYNDP,
    Infeed_consumers,
)


def correct_CH_demand_infeed_fcn(
    consumers_representing,
    T_list,
    Consumer_netflex_list,
    demand_tech_list,
    tech_infeed_consumers_list,
):
    """
    This function downward adjusts the demand and infeed time series of CH00_fixedconsumer.
    The aim is to keep the annual consumption in CH constant. The annual consumption in CH is given by the annual consumption of CH00_fixedconsumer and the annual consumption of consumers IDXX.
    Since the demand and infeed of IDXX are modelled in NETFLEX already, the demand and infeed of CH00_fixedconsumer should be corrected by substracting the demand and infeed of consumers IDXX.
    Input:
        consumers_representing: number of households in CH represented by one NETFLEX household
        T_list: list of time steps
        Consumer_netflex_list: list of consumers in NETFLEX
        demand_tech_list: list of demand technologies
        tech_infeed_consumers_list: list of infeed technologies
    Output:
        Demand_data: corrected demand time series of CH00_fixedconsumer
        Infeed_consumers: corrected infeed time series of CH00_fixedconsumer
    """

    # corecting demand and infeed time series  of CH00_fixedconsumer: by substracting the demand of consumers (IDXXX)
    for t in T_list:
        demand_t = sum(
            Demand_data.get((consumer_netflex, tech, t), 0)
            for consumer_netflex in Consumer_netflex_list
            for tech in demand_tech_list
        )
        Demand_data["CH00_fixedconsumer", "fixed", t] = (
            Demand_data_TYNDP["CH00_fixedconsumer", "fixed", t]
            - consumers_representing * demand_t
        )

        infeed_t = sum(
            Infeed_consumers.get((consumer_netflex, tech, t), 0)
            for consumer_netflex in Consumer_netflex_list
            for tech in tech_infeed_consumers_list
        )
        Infeed_consumers["CH00_fixedconsumer", "pvrf", t] = (
            Infeed_RES_TYNDP["CH00_fixedconsumer", "pvrf", t]
            - consumers_representing * infeed_t
        )
