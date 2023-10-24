# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 17:59:18 2023

@author: steph
"""

playPfad = "C:/Users/steph/Downloads/base"

import os

ret = []
total_size = 0
for (dirpath, dirs, files) in os.walk(playPfad):
    #print(dirpath)
    for filename in files:
        if os.path.exists(dirpath + "/" + filename):
            ret.append(filename)
            
print(ret)
