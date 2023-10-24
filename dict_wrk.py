# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 08:33:40 2023

@author: steph
"""

new_table = {
    'table_name' : '',
    'table_type' : 'scd2',
    'delete_detection' : 1,
    'dummy' : 1,
    'pk_name': '',
    'columns': []
}

new_field = {
    'column_name': 'feldname',
    'data_type': 'feldtyp',
    'mandatory': 'NULL',
    'bk': 0,
    'pk': 0,
    'default': '',
    'description': ''
}

wrk = {**new_table}

newline = {**new_field}
newline["column_name"] = "EINS"
print (new_field)
print (newline)

print(wrk['columns'])

wrk['columns'].append(newline)

print(wrk)

#my_input = ['Engineering', 'Medical'] 
#my_input.append('Science') 