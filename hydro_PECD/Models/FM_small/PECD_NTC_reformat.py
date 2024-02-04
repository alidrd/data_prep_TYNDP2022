# read the file Transfer Capacities_ERAA2021_TY2025.xlsx in original_datasets/ 
# and save the data in a dictionary transfer_capacities
import pandas as pd
import json

for year in [2025, 2030]:
    Line_list = []
    Map_line_node = {}
    ATC_exportlimit = {}
    ATC_importlimit = {}
    for sheet in ['HVAC', 'HVDC']:
        xls = pd.read_excel(r'input/NTC/Transfer_Capacities_ERAA2021_TY' + str(year) + '.xlsx',sheet_name=sheet, header=9)
        #for every even column in xls, save "HVAC + "_" + column name" in the Node_list, then save the value in the first row in Map_line_node["start_node"] and the value in the second row in Map_line_node["end_node"]
        # then save the rest of values in 
        #  in the column in the dictionary ATC_exportlimit, where the first key is the name of the line, "HVAC + "_" + column name", and the second key is t_1, t_2, ..., t_8760
        # find all unique elements in the columns of xls dataframe
        column_name_list = list(xls.columns[2:])
        # for every element in column_name_list whose name is X_Y, check if there is a column named Y_X
        # if there is, then delete the column named Y_X

        lines_and_reverse_lines = {}
        for column_name in column_name_list:
            if column_name not in lines_and_reverse_lines.values():           # if the line is not already in the dictionary, then add it, and check if there is a reverse line
                start, end = column_name.split("-")
                if end + '-' + start in column_name_list:
                    lines_and_reverse_lines[column_name] = True
                    column_name_list.remove(end + '-' + start)


        for column_name, exist_reverse in lines_and_reverse_lines.items():
            # separate column_name at the string " - "
            start, end = column_name.split("-")
            line_name = sheet + '_' + start + '_' + end
            columns_name_reverse = end + '-' + start
            Line_list.append(line_name)
            Map_line_node[line_name] = {}
            Map_line_node[line_name]["start_node"] = start
            Map_line_node[line_name]["end_node"] = end
            for i in range(len(xls[column_name])-3):
                ATC_exportlimit[line_name, "t_" + str(i+1)] = xls[column_name][i+3]
                ATC_importlimit[line_name, "t_" + str(i+1)] = xls[columns_name_reverse][i+3] if exist_reverse else 0

    # save Line_list in a json file
    with open(r'input/NTC/List_line_' + str(year) + '.json', 'w') as f:
        json.dump(Line_list, f, indent=4)

    # save the Map_line_node in a json file
    with open(r'input/NTC/Map_line_node_' + str(year) + '.json', 'w') as f:
        json.dump(Map_line_node, f, indent=4)
    
    # save the dictionary ATC_exportlimit in a json file. Note that the keys of the dictionary are tuples, so we need to converts a tuple (x, y) to a string in the form of "(x, y)"
    serialized_dict = {str(key): value for key, value in ATC_exportlimit.items()}
    with open(r'input/NTC/ATC_exportlimit_' + str(year) + '.json', 'w') as f:
        json.dump(serialized_dict, f, indent=4)

    # save the dictionary ATC_importlimit in a json file. Note that the keys of the dictionary are tuples, so we need to converts a tuple (x, y) to a string in the form of "(x, y)"
    serialized_dict = {str(key): value for key, value in ATC_importlimit.items()}
    with open(r'input/NTC/ATC_importlimit_' + str(year) + '.json', 'w') as f:
        json.dump(serialized_dict, f, indent=4)
