# -*- coding: utf-8 -*-
"""

Template Handling Objekt

Einlesen aller Templates eines Verzeichnisses ('./templates') in ein Dictionary
Zugriff via Template Name
Unterverzeichnisse im Basisverzeichnis werden auch eingelesen, die dienen als logische
Gliederung. Das bedeutet, dass Template Namen dort eindeutig sein müssen!

Zusätzlich: './custom/templates', das weitere Templates einliest, bzw bestehende überschreibt

Created on Mon Oct 23 12:30:05 2023

@author: steph
"""


from datetime import datetime as dt
import logging
import os
import time

from lib.dirmgmt import getSubdirs, getFiles, getAllFiles

printInfo = False

logging_file = './gen.log'

source_dir = './source/'
template_dir = './templates/'
macro_dir = './macros/'
job_dir = './jobs/'
custom_dir = './custom/'


run_templates = 'core'
tasks_name = 'tasks.yml'     # das YAML File mit den Task Definitionen, muss in jeder Template Grupppe vorhanden sein!


class BaseTmplFiles:
    
    def __init__(self):
        self.__baseDir = './'     #default
        self.__listFiles = []
        
    def set_base_dir(self, pBaseDir):
        self.__baseDir = pBaseDir

    def read_base_files(self, pFilter):
        self.__listFiles = []
        vRet, vFiles = getAllFiles(self.__baseDir, pFilter)
        if vRet==0:
            self.__listFiles = vFiles
        return self.__listFiles
            
            

class Templates(BaseTmplFiles):
        
    def __init__(self):
        
        self.__templateDir = './templates/'     #default
        self.__customDir = './custom/'
        self.__lstTmpl = {}
        
    def get_all_templates(self):
        return self.__lstTmpl
        
    def get_template_dir(self):
        return self.__templateDir
        
    def get_custom_dir(self):
        return self.__customDir
    
    def set_template_dir(self, pTmplDir):
        self.__templateDir = pTmplDir
        
    def set_custom_dir(self, pCustDir):
        self.__customDir = pCustDir
        
    def read_templates(self):
        self.set_base_dir(self.__templateDir)
        self.__lstTmpl = self.read_base_files('*.tmpl')
        #jetzt gegebenenfalls mit Custom Einträgen ergänzen
        
        
            
    
    
vTemplates = Templates()
print(vTemplates.get_all_templates())

vTemplates.read_templates()



