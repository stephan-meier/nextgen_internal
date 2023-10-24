# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 10:27:07 2023

@author: steph
"""


pipeline(
('sta_90er_view',             sta_schema_name, tmpl_sta_90er_view_SQL),
('sta_91er_view',             sta_schema_name, tmpl_sta_91er_view_SQL),
('sta_table',                 sta_schema_name, tmpl_sta_table_SQL),
('dwh_table',                 dwh_schema_name, tmpl_dwh_table_SQL),
('rep_views',                 rep_schema_name, tmpl_rep_views_SQL),
('proc_sta_dummy',            sta_schema_name, tmpl_proc_sta_dummy_SQL),
('proc_sta_full_load',        sta_schema_name, tmpl_proc_sta_full_load_SQL),
('proc_sta_delete_detection', sta_schema_name, tmpl_proc_sta_delete_detection_SQL)
)


sta_90er_view_PLAN_B(sta_schema_name, src_table, jetztString)
sta_91er_view_PLAN_B(sta_schema_name, src_table, jetztString)
sta_table_PLAN_B(sta_schema_name, src_table, jetztString)
dwh_table_PLAN_B(dwh_schema_name, src_table, jetztString)
rep_views_PLAN_B(rep_schema_name, src_table, jetztString)
proc_sta_dummy_PLAN_B(sta_schema_name, src_table, jetztString)
proc_sta_full_load_PLAN_B(sta_schema_name, src_table, jetztString)
proc_sta_delete_detection_PLAN_B(sta_schema_name, src_table, jetztString)