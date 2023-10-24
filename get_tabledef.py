# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 11:04:14 2023

@author: steph
"""

from datetime import datetime as dt
import logging
import pandas as pd
import pyodbc
import jinja2

doExecute = True
printInfo = False

logging_file = './gen.log'

# TODO: als Konfig File auslagern
sta_schema_name = "stg"
dwh_schema_name = "dwh"
rep_schema_name = "rep"


tmpl_get_tables_SQL = """
select * from INFORMATION_SCHEMA.TABLES
"""



########## SQL SKRIPT AUSFÜHREN ##########
def execute_statements(sql_script):
    # init DB Connection
    server = "itxchdm.switzerlandnorth.cloudapp.azure.com"
    database = "NGDWA"
    username = "chdm"
    password = "IT-Logix32"

    ret = 0
    answer = ''

    if doExecute:

        try:
            conn = pyodbc.connect(
                "DRIVER={SQL Server};SERVER=" + server + ";DATABASE=" + database + ";UID=" + username + ";PWD=" + password)

            # Template SQL Ausführung
            # sql = "select count(*) cnt from dwh.dim_Patient"
            # cursor = conn.cursor()
            # result = pd.read_sql_query(sql, conn)
            # cnt = int(result.cnt[0])
            # print("count: " + str(cnt))
            # cursor.close()

            # cursor = conn.cursor()
            # cursor.execute(script)
            with conn.cursor() as cursor:
                for statement in sql_script.split(";"):
                    if printInfo:
                        print(statement)
                    if len(statement) > 0:
                        cursor.execute(statement)
                        answer = cursor.fetchall()
                        conn.commit()
        except pyodbc.DataError as err:
            ret = 'pyodbc: Data Error! '  + err.args[1]
            print(ret)
        except pyodbc.OperationalError as err:
            ret = 'pyodbc: Operational Error! '  + err.args[1]
            print(ret)
        except pyodbc.IntegrityError as err:
            ret = 'pyodbc: Integrity Error! ' + err.args[1]
            print(ret)
        except pyodbc.InternalError as err:
            ret = 'pyodbc: Internal Error! ' + err.args[1]
            print(ret)
        except pyodbc.ProgrammingError as err:
            ret = 'pyodbc: Programming Error! ' + err.args[1]
            print(ret)
        except pyodbc.NotSupportedError as err:
            ret = 'pyodbc: NotSupported Error! ' + err.args[1]
            print(ret)
        else:
            cursor.close()
            conn.close()
    else:
        print('--- SQL Script ------------------------------------------------')
        print(sql_script)
        print('---------------------------------------------------------------')

    return ret, answer



def build_query(template, **kwargs):    
    script = ''    
    try:
        environment = jinja2.Environment()
        template = environment.from_string(template)
        script = template.render()
    except jinja2.TemplateError as error:
        logger.error("In build_query gibt es einen Jinja Fehler: " + str(error))
    except:
        logger.error("In build_query gibt es einen unbekannten Fehler.")
    return(script)
    
    
#------------------------------------- MAIN ----------------------------------------------------    
# Logging initialisieren
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(logging_file)
    formatter = logging.Formatter('%(asctime)s -%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

#logger.debug("Debug Info")
logger.info("Prozess gestartet")
#logger.warning("Irgendetwas ist nicht gut.")
#logger.error("Da ist ein Fehler!")
#logger.critical("Etwas wirklich schlimmes ist passiert!!")
    

tmplSQL = tmpl_get_tables_SQL
sql = build_query(tmplSQL)
print(sql)
ret, ans = execute_statements(sql)
print(ans)
    