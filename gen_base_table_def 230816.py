# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 06:58:36 2023

@author: steph
"""

# WICHTIG: ein Unterverzeichnis 'base' muss schon existieren!

# Annahme: jede Tabelle hat maximal einen Index (PK)!! Bis jetzt ist das in CDWH so.
# Annahme: jeder PK besteht aktuell aus einem Feld. Das gilt nur für das aktuelle CDMH Modell. Entsprechend ist das Parsing einfacher aufgebaut. 
#          Die Generatortemplates können auch zusammengesetzte PKs abbilden.

import xmltodict
import json
import pprint

saveJson = False        # einzelnes json File direkt aus XML mit allen Definitionen schreiben
saveTableList = False   # einzelnes json File mit Definitionen für alle Files für den Generator schreiben
genTableFiles = True    # Tabellendefinitionen in einzelne Files schreiben
printTable = ''   #'dim_CaseAdministrative'

xmlInFile = "./PDM_CHDM.pdm"
jsonOutFile = "./PDM_CHDM.json"
tableListFile = "./table_list.json"
dirTableFiles = "./base/"
    
table_list = []  
    
def get_table_info(p_table):
    # eine einzelne Tabellendefinition aus dem Dictionary lesen
    ret = ''
    position = 0
    for p in table_list:
        if p['table_name'] == p_table:
            ret = p
            break
        position += 1
    return ret


def write_base_table(p_table_doc):
    # einzelne Tabellendefinition als json File schreiben
    ret = 0
    try:
        target = dirTableFiles + p_table_doc['table_name'] + '.json'
        f = open(target,"w")
        json.dump(p_table_doc,f)
        f.close()
    except:
        ret = 1
    return ret


def remove_nested_keys(dictionary, keys_to_remove):
    # Key Values aus Dictionary löschen, wird für at_id (PKs) benötigt
    new_dict = {}

    for key, value in dictionary.items():
        if key not in keys_to_remove:
            if isinstance(value, dict):
                new_dict[key] = remove_nested_keys(value, keys_to_remove)
            else:
                new_dict[key] = value

    return new_dict


with open(xmlInFile, encoding='utf-8') as fd:
    doc = xmltodict.parse(fd.read(),process_namespaces=True)
    
if saveJson:
    file=open(jsonOutFile,"w")
    json.dump(doc,file)
    file.close()
    
m_t = doc["Model"]["object:RootObject"]["collection:Children"]["object:Model"]["collection:Tables"]


for t in m_t["object:Table"]:
    tabellen_name = ''
    nt = {'table_name' : '',
        'at_id': '',
        'table_type' : 'scd2',
        'delete_detection' : 1,
        'dummy' : 1,
        'pk_name': '',
        'columns': []}
    nt["table_name"] = t["attribute:Name"]
    nt["at_id"] = t["@Id"]
    tabellen_name = t["attribute:Name"]
    print(tabellen_name)
    
    #pk's sammeln
    pk_fld_id = ''
    pk_name = ''
    pk = t.get("collection:PrimaryKey", "")
    if pk != "":
        pko = pk['object:Key']['@Ref']
        #und nun der Index
        key = t["collection:Keys"]["object:Key"]
        if pko == key['@Id']:     #das ist der richtige Index
            pk_name = key['attribute:Name']
            pk_fld_id = key['collection:Key.Columns']['object:Column']['@Ref']
        
    nt["pk_name"] = pk_name
    
    for c in t["collection:Columns"]["object:Column"]:
        nf = {'column_name': 'feldname',
        'at_id': '',         
        'data_type': 'feldtyp',
        'date_dim': 1,             #Falls Datentyp Datum, sollen die Datums/Zeitdimensionen gebildet werden?
        'mandatory': 'NULL',
        'bk': 0,
        'pk': 0,
        'default': '',
        'description': '',
        'extended': ''}
        mand = "NULL"
        if c.get("attribute:Column.Mandatory", "0") == "1":
            mand = "NOT NULL"
        #print(c.get("attribute:Name", "N/A"), "/", c.get("attribute:DataType", "N/A"), "/", c.get("attribute:Comment", ""), "/", mand, "/", c.get("attribute:ExtendedAttributesText", ""))
        nf["column_name"] = c.get("attribute:Name", "N/A")
        nf["at_id"] = c.get("@Id", "")
        nf["data_type"] = c.get("attribute:DataType", "N/A")
        nf["mandatory"] = mand
        nf["description"] = c.get("attribute:Comment", "")
        nf["extended"] = c.get("attribute:ExtendedAttributesText", "")
        
        if nf["at_id"] == pk_fld_id:
            nf['pk'] = 1
            
        #bk Logik: falls ein Feld den Namen "tabellenname" & "_bk" hat, wird das bk Flag auf 1 gesetzt
        if nf["column_name"] == tabellen_name + '_bk':
            #ein BK wurde gefunden!
            nf['bk'] = 1
        
        nf_c = remove_nested_keys(nf, 'at_id')    # Referenz ID's raus, die braucht es nicht mehr
        nt['columns'].append(nf_c)

    nt_c = remove_nested_keys(nt, 'at_id')
    
    print('-------------------------------------------------------------')
    
    table_list.append(nt_c)
    if genTableFiles:
      write_base_table(nt_c)  

if saveTableList:
    file=open(tableListFile,"w")
    json.dump(table_list,file)
    file.close()

if printTable != '':       # falls da ein Tabellenname steht: Definition ausgeben 
    #print(get_table_info(printTable))
    pp = pprint.PrettyPrinter(depth=4, sort_dicts=False)
    pp.pprint(get_table_info(printTable))
        
