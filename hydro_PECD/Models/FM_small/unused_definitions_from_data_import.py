Tech_list.extend(tech_list_data_import)
Tech_list.extend(["pvrf", "windon", "windof"])

# create a list of assets/plants that are not assigned to a consumer - this is useful for constraints
Plant_list_no_consumer = [p for p in Plant_list if p not in [item for sublist in Map_consumer_plant.values() for item in sublist]]
Consumer_list_with_plants = [c for c in Consumer_list if c in Map_consumer_plant.keys()]   
for tech in Tech_list:
    Map_tech_plant[tech] = [p for p in Plant_list if Map_plant_tech[p]==tech]



consumer_connection_list = []  # list of all connections to the consumer - useful for constraints
if consumer_connection_limit: # if True, then the number of connections to the consumer is limited #TODO: below not tested yet
    Map_consumer_node_grid = Map_consumer_node.copy()

    # a consumer (e.g., consumer_01) is originally connected to a node (e.g., CH_01), but now we need to 1) first remove it from the node and then 2)create a new node for the consumer (a bit lower)
    # 1) remove consumer from the node: remove all values in Map_node_consumer that are in Consumer_list_limitted_trade
    for node in Node_list:
        nodes_to_be_removed = []
        for item in Map_node_consumer[node]:
            if item in Consumer_list_limitted_trade:
                nodes_to_be_removed.append(item)
        for item_r in nodes_to_be_removed:
            Map_node_consumer[node].remove(item_r)
    Map_node_plant = {}  # for each nodes, which plants are connected to that node - needs Node_list Plant_list Map_plant_node - useful for constraints
    counter = 1
    for consumer in Consumer_list_limitted_trade:
        node_name = "node_" + consumer
        Node_list.append(node_name)                      # 2) create a new node for the consumer
        Map_node_consumer[node_name] = consumer
        Map_consumer_node[consumer] = node_name
        if consumer in Map_consumer_plant.keys():
            for plant in Map_consumer_plant[consumer]:   # assigning plants of the consumer to its node
                Map_plant_node[plant] = node_name        # add the consumer to the Map_plant_node


        # add a new item to lineATC_list named "connection_{counter}_{consumer}_{node_conntected}" where counter is a number that increases with each new connection, consumer is the name of the consumer and node_connected is the node where the consumer is connected
        # find the node connected to the consumer
        connention_name = "connection_" + str(counter) + "_" + consumer + "_" + Map_consumer_node_grid[consumer]
        LineATC_list.append(connention_name)
        consumer_connection_list.append(connention_name)
        Map_line_node[connention_name] = {"start_node": node_name, "end_node": Map_consumer_node_grid[consumer]}
        for t in T_list:
            ATC_exportlimit[(connention_name,t)] = Consumer_import_max[consumer]
            ATC_importlimit[(connention_name,t)] = Consumer_export_max[consumer]
        counter += 1
    for node in Node_list:
        Map_node_plant[node] = [p for p in Plant_list if Map_plant_node[p]==node]
    # for every line  ------------------------------------------------------- processing (copied from above) 
    Map_node_exportinglineATC = {}   #  determines for each node, the lines(ATC) are connected to it that are start node  - needs Map_line_node Node_list - useful for constraints
    Map_node_importinglineATC = {}
    # sample output  for Map_line_node ={"line_01_CH01_EU01" : {"start_node": "CH_01", "end_node": "EU_01"}} - Map_node_exportinglineATC={'CH_01': ['line_01_CH01_EU01'], 'EU_01': []} - Map_node_importinglineATC = {'CH_01': [], 'EU_01': ['line_01_CH01_EU01']}
    for node in Node_list:
        Map_node_exportinglineATC[node] = [l for l in LineATC_list if node==Map_line_node[l]["start_node"]] 
        Map_node_importinglineATC[node] = [l for l in LineATC_list if node==Map_line_node[l]["end_node"]] 
else:
    Consumer_list_limitted_trade = []
# %%
