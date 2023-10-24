# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 17:27:28 2023

@author: StephanMeier
"""


source_dir = './source/'
template_dir = './templates/'
run_templates = 'core'

def read_template(p_filename):
    ret = ""
    try:
        f = open(p_filename, encoding='utf-8-sig')
        ret = f.read()
        f.close()
    except:
        logger.error("Fehler in read_template. Parameter: " + p_filename) 
    
    return ret

s = read_template(template_dir + run_templates + '/' + 'tmpl_sta_90er_view_SQL.tmpl')
print(s)