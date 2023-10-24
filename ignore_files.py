# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 15:27:28 2023

@author: steph
"""

import os
from fnmatch import fnmatch

some_dir = 'D:/'
ignore_list = ['*.tmp', 'tmp/', '*.py']
for dirname, _, filenames in os.walk(some_dir):
    for filename in filenames:
        should_ignore = False
        for pattern in ignore_list:
            if fnmatch(filename, pattern):
                should_ignore = True
        if should_ignore:
            print ('Ignore', filename)
            continue

print('----------------------------------------------')         
     
"""   
for filename in filenames:
    if any(fnmatch(filename, pattern) for pattern in ignore_list):
        print ('Ignore', filename)
        continue
"""
        
print('----------------------------------------------')      
        
        
import os, fnmatch
l = fnmatch.filter(os.listdir('D:/'), '*.xml')
print(l)