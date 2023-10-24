# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 07:55:34 2023

@author: steph
"""

import os
import logging




logging_file = 'D:/wrx/py_crash.log'

print("Logging to", logging_file)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    
    # create a file handler
    handler = logging.FileHandler(logging_file)
    #handler.setLevel(logging.DEBUG)
    
    # create a logging format
    formatter = logging.Formatter('%(asctime)s -%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # add the handlers to the logger
    logger.addHandler(handler)



def eineProzedur():
    ret = 0
    logger.info("eineProzedur: eine Prozedur")
    
    return ret

logger.debug("MAIN: Start of the program")
logger.info("MAIN: Doing something")
logger.warning("MAIN: Dying now")
logger.error("MAIN: Error !!")
logger.critical("Etwas wirklich schlimmes ist passiert!!")

x = eineProzedur()