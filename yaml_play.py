# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 19:20:43 2023

@author: StephanMeier
"""

import yaml

# dict objects
user_details = {'UserName': 'Alice',
                'phone': 3256,
                'Password': 'star123*',
                'TablesList': ['EmployeeTable', 'SoftwaresList', 'HardwareList']}


task_details = {'Version': 2, 
 'schemas': [{'name': 'sta_schema_name', 'db_schema': 'stg'}, {'name': 'dwh_schema_name', 'db_schema': 'dwh'}, {'name': 'rep_schema_name', 'db_schema': 'rep'}], 
 'tasks': [{'name': 'sta_90er_view', 'ziel_schema': 'sta_schema_name', 'quell_schema': 'sta_schema_name', 'tmpl_name': 'tmpl_sta_90er_view_SQL'}, 
           {'name': 'sta_91er_view', 'ziel_schema': 'sta_schema_name', 'quell_schema': 'sta_schema_name', 'tmpl_name': 'tmpl_sta_91er_view_SQL'}]
 }

print(yaml.dump(task_details, indent=4, default_flow_style=False))
