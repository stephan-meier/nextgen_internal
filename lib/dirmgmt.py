# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 12:25:48 2023

@author: steph

getSubdirs('D:/work/')
getFiles('D:/pyplay/template/core/', pFilter='*.tmpl')

"""

import os
import fnmatch
import pathlib
import datetime





def isDir(pPfad):
    ret = False
    if os.path.isdir(pPfad):
        ret = True
    return ret


def isFile(pFile):
    ret = False
    if os.path.isfile(pFile):
        ret = True
    return ret


def dir_size_scan(root_dir):
    ret = []
    total_size = 0
    for (dirpath, dirs, files) in os.walk(root_dir):
        #print(dirpath)
        for filename in files:
            if os.path.exists(dirpath + "/" + filename):
                eintrag = {}
                stats = os.stat(dirpath + "/" + filename)
                file_size = stats.st_size
                date_object = datetime.datetime.fromtimestamp(stats.st_ctime)
                file_date = date_object.strftime('%Y-%m-%d-%H:%M')
                eintrag["pfad"] = dirpath
                eintrag["file"] = filename
                eintrag["groesse"] = file_size
                eintrag["datum"] = file_date
                #sx = filename
                #eintrag["checkfield"] = sx + '/' + str(file_size)
                eintrag["partpfad"] = dirpath[len(root_dir):]
                
                total_size += file_size
                ret.append(eintrag)
    return ret


def getSubdirs(pPfad):
    # pPfad mit abschliessendem /
    ret = 0
    dirsList = []
    if os.path.exists(pPfad):    
        vDirs = os.listdir(pPfad)
        if len(vDirs)>0:
            for i in vDirs:
                if isDir (pPfad + i):
                    dirsList.append(i)         
    else:
        ret = 1
    return ret, dirsList


def getFiles(pPfad, pFilter='*.*'):
    # pPfad mit abschliessendem /
    ret = 0
    filesList = []
    if os.path.exists(pPfad):    
        vFiles = fnmatch.filter(os.listdir(pPfad), pFilter)
        if len(vFiles)>0:
            for i in vFiles:
                if isFile (pPfad + i):
                    filesList.append(i)         
    else:
        ret = 1
    return ret, filesList    


def getAllFiles(pPfad, pFilter='*.*'):     # alle Files, d.h. rekursiv durch Unterverzeichnisse
    # WIP
    ret = 0
    filesList = []
    if os.path.exists(pPfad):
        listeAll = dir_size_scan(pPfad)
        if len(listeAll) > 0:
            for item in listeAll:
                if fnmatch.fnmatch(item['file'], pFilter):
                    filesList.append(item)
    else:
        ret = 1
    return ret, filesList                
    

    
    
    