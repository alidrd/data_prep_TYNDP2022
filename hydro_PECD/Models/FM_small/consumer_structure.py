import os
import json

path_consumer_structure = f'C:\\Models\\Future_Markets\\cons_structure_attempt'
os.chdir(path_consumer_structure)
os.listdir(path_consumer_structure)


character_consumer_0001 = {
    'consumer_id': 'abc123', 
    'node': ['CH01', 'CH02'], 
    'optimization': ['max_util', 'min_cost'], 
    'tariff_cons': 'flat',
    'tariff_feed': 'dyamic',
    'basedemand': {
        't1': 10, 
        't2': 10, 
        't3': 10, 
        't4': 10, 
        't5': 10, 
        't6': 10, 
        't7': 10, 
        't8': 10, 
        't9': 10, 
        't10': 10, 
        't11': 10, 
        't12': 10, 
        't13': 10, 
        't14': 10, 
        't15': 10, 
        't16': 10, 
        't17': 10, 
        't18': 10, 
        't19': 10, 
        't20': 10, 
        't21': 10, 
        't22': 10, 
        't23': 10, 
        't24': 10}, 
    'assets': {
        'c01_hp_01': {
            'type' : 'hp_type_1', 
            'max_demand': 100, 
            'season': {
                'winter':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]},
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'spring':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'summer':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'fall':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} } }}, # end single asset 
        'c01_hp_02': {
            'type' : 'hp_type_2',
            'max_demand': 100, 
            'season': {
                'winter':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]},
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'spring':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'summer':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} },
                'fall':{
                    'workday' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]}, 
                    'weekend' : {
                        'timehorizon': [(1,8), (9,16), (17,24)],
                        'utility_c0': [1,2,3],
                        'utility_c1': [1,2,3]} } }}, # end single asset 
        'c01_ev_01': {
            'type' : 'ev_type_2',
            'max_demand': 100, # / "size"
            'charging_type' : 'v1g', 
            'workday' : {
                'timehorizon': [(1,8), (9,16), (17,24)],
                'utility_c0': [1,2,3],
                'utility_c1': [1,2,3]}, 
            'weekend' : {
                'timehorizon': [(1,8), (9,16), (17,24)],
                'utility_c0': [1,2,3],
                'utility_c1': [1,2,3]}  }, # end single asset
        'c01_pv_01': {
            'type' : 'pv_type_3'}, # end single asset
        'c01_pv_02': {
            'type' : 'pv_type_1'}, # end single asset
        'c01_ba_01': {
            'type' : 'ba_type_1', 
            'max_demand' : 100 } # end single asset

        

    } # end assets 
} # end dictionary

with open("character_consumer_0001.json", "w") as file: 
    json.dump(character_consumer_0001, file)
    print("json exported +1")



tech_specs = {
    'STILL_MISSING': [
        'Cost component for eacht tech_type', 
        'efficiency factors for all technologies', 
        'destinciont between consumer & producer necessary?'
    ],
    'hp':{
        'class_name': 'heat pump', 
        'hp_type_1': {'min_demand': 5, 'max_demand': 15 },
        'hp_type_2': {'min_demand': 5, 'max_demand': 15 }, 
        'hp_type_3': {'min_demand': 5, 'max_demand': 15 }}, # end hp
    'ev':{
        'class_name': 'electric vehicle', 
        'ev_type_1': {
            'charging_option': ['v1g', 'v2g', 'stupid charging'] ,
            'charging_fac': 5, 
            'discharging_fac': 5, 
            'min_demand': 5, 
            'max_demand': 15 }, 
        'ev_type_2': {
            'charging_option': ['v1g', 'v2g', 'stupid charging'],
            'charging_fac': 5, 
            'discharging_fac': 5, 
            'min_demand': 5, 
            'max_demand': 15 },
        'ev_type_3': {
            'charging_option': ['v1g', 'v2g', 'stupid charging'],
            'charging_fac': 5, 
            'discharging_fac': 5, 
            'min_demand': 5, 
            'max_demand': 15}}, # end ev
    'pv':{
        'class_name': 'solar / photovoltaic',
        'pv_type_11':{
            'mounting':'roof',
            'surface_area': [1,2,3], 
            'alignment': [1,2,3],
            'max_output': 5},
        'pv_type_12':{
            'mounting':'roof',
            'surface_area': [1,2,3],
            'alignment': [1,2,3],
            'max_output': 5}, 
        'pv_type_21':{
            'mounting':'facade',
            'surface_area': [1,2,3], 
            'alignment': [1,2,3],
            'max_output': 5},
        'pv_type_22':{
            'mounting':'facade',
            'surface_area': [1,2,3],
            'alignment': [1,2,3],
            'max_output': 5}}, # end pv
    'ba':{
        'class_name': 'battery', 
        'ba_type_1':{
            'charging_fac': 5, 
            'discharging_fac': 5, 
            'storage_capacity': 5}, 
        'ba_type_2':{
            'charging_fac': 5, 
            'discharging_fac': 5, 
            'storage_capacity': 5}},  # end ba
    'gas':{},
    'dam':{},
    'psp':{}
    
}# end dictionary


with open("tech_specs.json", "w") as file: 
    json.dump(tech_specs, file)
    print("json exported +1")





print(f' \n \n *{20*"="}* \n finished running script \n *{20*"="}*')