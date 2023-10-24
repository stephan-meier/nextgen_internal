import pyodbc
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import requests
import pprint

import jinja2

doExecute = False
printInfo = False

# Beispiel SqlDBM --> TODO Token ersetzen
print("*************SqlDBM API letzte DDL version auslesen. START...")

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ijg4ZWJlM2M1LTBhMTAtNDkyZi04YjNkLTBiNTU0YjI1Njk0ZCIsIm5iZiI6MTY4Nzc1NjE0NiwiZXhwIjoxNzAzMzk0NTQ2LCJpYXQiOjE2ODc3NTYxNDYsImlzcyI6InNxbGRibS5jb20iLCJhdWQiOiJzcWxkYm0uY29tIn0.Xp7I3SUiLazE95C5msUvYS9WfDakGL5sUoEnwloBLY8"
url = "https://api.sqldbm.com/projects/257156/revisions/last/ddl"
headers = {
    "accept": "application/json",
    "Authorization": token
}
#response = requests.get(url, headers=headers)
#print(response.text)
#response_json = response.json()
print("SqlDBM DDL für dim_Patient ausgeben:")
# TODO: Objekt Nummer anhand Input rausfinden, z.B. für dim_Patient = 63
#pprint.pprint(response_json['data']['dbObjects'][63]['objectDdl'])

#str(response_json['data']['dbObjects'][63]['objectDdl']).replace("\r\n","")


print("***************...SqlDBM API letzte DDL version auslesen. ENDE")

# Ende Beispiel SqlDBM

# --> Das Interface kann sein:
#       - eine API eines Modellierungstool (z.B. SqlDBM API oder Powerdesigner Repository)
#       - die DB mit extendedproperties (oder annotations > kann pro DB System unterschiedlich sein)
#       --> was wäre das bei Lakehouse?


# Pseudo Code
# 1) Prompt --> Generierung für "welche(s) Objekt (1-n), oder alle Objekte" eingeben
# 2) Read Output aus API (hier response String), Filter eingegebener Prompt auf Response oder mach jetzt den API Call
# 3) Read Extended Attributes on Table/Column level -->     scd1/scd2, delete detection (geht nur im Full load), dummy, Early Arrive Felder
#                                                           Delta Konfiguration / Partition Konfiguration

# TODO: als Konfig File auslagern
sta_schema_name = "stg"
dwh_schema_name = "dwh"
rep_schema_name = "rep"

######## Diese Informationen müssen vom Interface des Modellierungstools eingelesen werden - START ######
table_name = "dim_Patient"
table_type = "scd2"
delete_detection = "yes"
dummy = "yes"
src_bk_column = [{
            'column_name': 'dim_Patient_bk',
            'data_type': 'nvarchar(56)',
            'mandatory': 'not null',
            'bk': 1
        }]
bk_column = pd.DataFrame(src_bk_column)

src_column_list = [{
            'column_name': 'dim_SourceSystem_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'InternalId',
            'data_type': 'nvarchar(50)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'FirstName',
            'data_type': 'nvarchar(255)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'LastName',
            'data_type': 'nvarchar(255)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'BirthDate',
            'data_type': 'datetime',
            'mandatory': 'null',
            'bk': 0
        },
        {
            'column_name': 'dim_Country_ResidenceCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'dim_Country_BirthCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'dim_Country_CitizenshipCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0
        },
        {
            'column_name': 'GestationalAgeInDays',
            'data_type': 'integer',
            'mandatory': 'null',
            'bk': 0
        }
    ]
column_list = pd.DataFrame(src_column_list)

early_arrive_column_list = {
    "table": [
        {
            "ref_table_name": "dim_SourceSystem",
            "column_name": ["dim_SourceSystem_bk"]
        },
        {
            "ref_table_name": "dim_Country",
            "column_name": ["dim_Country_ResidenceCountry_bk", "dim_Country_BirthCountry_bk","dim_Country_CitizenshipCountry_bk"]
        }
    ]
}

"""
print(f"{sta_schema_name=}")
print(f"{dwh_schema_name=}")
print(f"{rep_schema_name=}")
print(f"{table_name=}")
print(f"{table_type=}")
print(f"{delete_detection=}")
print(f"{dummy=}")
print(f"{bk_column=}")
print(f"{column_list=}")
print(f"{early_arrive_column_list=}")
"""


src_table = {
    'table_name' : 'dim_Patient',
    'table_type' : 'scd2',
    'delete_detection' : 1,
    'dummy' : 1,
    'pk_name': 'dim_Patient_pk',
    'columns': [{
            'column_name': 'dim_Patient_bk',
            'data_type': 'nvarchar(56)',
            'mandatory': 'not null',
            'bk': 1,
            'pk': 1,
            'default': '',
            'description': 'der Businesskey'
        },
        {
            'column_name': 'dim_SourceSystem_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'InternalId',
            'data_type': 'nvarchar(50)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'FirstName',
            'data_type': 'nvarchar(255)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'LastName',
            'data_type': 'nvarchar(255)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'BirthDate',
            'data_type': 'datetime',
            'mandatory': 'null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'dim_Country_ResidenceCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'dim_Country_BirthCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'dim_Country_CitizenshipCountry_bk',
            'data_type': 'nvarchar(5)',
            'mandatory': 'not null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        },
        {
            'column_name': 'GestationalAgeInDays',
            'data_type': 'integer',
            'mandatory': 'null',
            'bk': 0,
            'pk': 0,
            'default': '',
            'description': ''
        }
    ]
}


######## Diese Informationen müssen vom Interface des Modellierungstools eingelesen werden - ENDE ######


# 4) Generate DWH (PSA Pattern sind ab sta-Tabelle ein subset von diesen Patterns):
#    Sammle alle extended attributes auf Ebene Tabelle (scd1/scd2, delete detection oder Delta Konfigruation / Partition Konfiguration)
#       DWH DDL Generierung:
#           > erzeuge DDLs
#               > sta-Tabelle
#                   > Felder: Load-ID Feld, delete detection Flag, Date/Time Field BKs --> done
#                   > PK auf BK --> done
#                   > Partitioning: gemäss Partition Konfiguration --> muss nicht im ersten Release erstellt werden --> TODO später
#               > 90er-View Hülle (nur wenn sie nicht bereits besteht, ansonsten skip) --> done
#               > 91er-View: Date/Time Field BKs, NOT NULL Handling für mandatory fields --> done
#               > dwh-Tabelle
#                   > Felder: sid, batch_run_id_insert, batch_run_id_update, Date/Time Field BKs, scd2 Felder (validFrom, ValidTo, InsertDate, UpdateDate, is_current), is_deleted, is_early_arrive, early_arrive_table --> done
#                   > Indexe: PK auf SID, Index auf BK, Indexe auf FKs (Early Arrive column_list) --> TODO später
#                   > Partitioning: gemäss Partition Konfiguration --> muss nicht im ersten Release erstellt werden --> TODO später
#                   ??? was passiert wenn die Tabelle schon vorhanden ist? Wie wird das Alter Skript erzeugt? Wird überhaupt ein Alter Skript erzeugt oder die Tabelle immer neu erstellt?
#                       1) Wenn die Tabelle neu erstellt wird auf DEV und somit geleert wird, dann haben wir das Problem, dass die DEV-DB fast immer leere DWH Tabellen hat, was nicht gut ist.
#                       Man könnte den Generator so gestalten, dass er immer ein rename Table erzeugt und die neuen not null Felder immer mit den dummy Werten initialiseirt.
#                           > Falls dann der Entwickler einen Intialwert einbauen muss, dann muss er dies mittels eines post-skriptes von hand schreiben.
#                             Das Handling kann dann unterschiedlich pro Change sein
#                       2) Man könnte auch eine Generierungs-DB erstellen und dann über den DevOps Deploy Prozess das Delta bestimmen und dann über manuelle pre-/post Skripte die Daten "retten"
#                   --> Daher die Überlegung, dass die dwh-scd2-Tabelle von Hand in die DB engineered wird.
#                       Problem hierbei ist aber, dass man dann alle extended Attributes auch auf der DB braucht, da sonst der Workflow für die Generierung unlogisch ist
#                           (Modellierung > manuelles foreward enginnering > generierung) --> Nachteil: die dwh-scd2-tabelle muss bereits alle Felder in der Modellierung beinhalten, was nicht gut ist,
#                           was wiederum bedeutet, dass man als API immer die DB nimmt. Was aber wieder ein Problem ist, wenn man ein Lakehouse baut.
#                       3) Vor der Generierung muss immer ein rename der bestehenden Tabelle generiert werden. --> done
#                           Der Generator füllt die Daten aber nicht zurück. Dafür muss der Entwickler ein manuelles Post-Skript erstellen --> Das ist die Lösung!!!
#               > rep cur, cid, fhi Views --> done
#       DWH Prozeduren (Kombi: scd2, [delete detection], [dummy])
#           > SP-sta-full-load:                     1:1 Kopie der 91er View in die sta-Tabelle --> done --> TODO später Optimierung Index Drop / Recreate Index
#           > SP-sta-delete-detection:              Delete Detection (sta-BK not exists in cur-View --> insert into sta-Tabelle mit delete_flag = 1) --> done
#           > SP-sta-dummy                          bei history Tabellen (Unterscheidung dim fakt noch nötig?) --> done
#           > SP-dwh-scd2                           Upsert aus sta- in dwh-Tabelle. Vergleich über alle Felder oder hash (wo wir hash berechnet?) --> TODO
#       DWH Prozeduren (Kombi: scd1, [delete detection], [dummy])
#           > SP-sta-full-load:                     1:1 Kopie der 91er View in die sta-Tabelle
#           > SP-sta-delete-detection:              Delete Detection (sta-BK not exists in cur-View --> insert into sta-Tabelle mit delete_flag = 1)
#           > SP-sta-dummy                          bei history Tabellen (Unterscheidung dim fakt noch nötig?)
#           > SP-dwh-scd1 (full load)               Merge aus sta- in dwh-Tabelle. Vergleich über alle Felder oder hash (wo wird hash berechnet?) --> TODO
#       DWH Prozeduren (Kombi: scd1, delta overlap without delete)
#           > SP-sta-delta-load:                    read delta trigger --> datum oder key gefilterte 1:1 Kopie aus der 91er View in die sta-Tabelle --> Update delta trigger --> TODO
#           > SP-dwh-scd1-overlap_without_delete:   Merge aus sta- in dwh-Tabelle. Vergleich über alle Felder oder hash (wo wird hash berechnet?) --> gleiches Pattern wie SP-dwh-scd1 --> TODO
#       DWH Prozeduren (Kombi: scd1, delta overlap with delete)
#           > SP-sta-delta-load:                    read delta trigger --> datum oder key gefilterte 1:1 Kopie aus der 91er View in die sta-Tabelle --> Update delta trigger
#           > SP-dwh-scd1-overlap-with-delete       predelete overlap > insert as select from sta into dwh --> TODO
#       DWH Prozeduren (Kombi: scd1, delta partitioned)
#           > SP-sta-delta-load:                    read Partition delta trigger --> datum oder key gefilterte 1:1 Kopie aus der 91er View in die partitioniert sta-Tabelle --> Update delta trigger
#           > SP-dwh-scd1-switch-partition:         Switch Partition from sta to dwh --> TODO
#       --> diverse weitere Delta Patterns

# offen:
#           1) komplexe staging Logik mit mehreren Views aufeinander, welche zwischenzeitlich gestaged werden müssen
#               --> Idee Generator prüft, ob eine ##er-View eine zugehörtige Tabelle mit NC-postfix -sta hat und generiert dafür eine SP-sta-[Name]-## (Nachteil: Generierung über NCs --> könnte man aus Pragmatismus zulassen)
#           2) always data (Schema switching)

########## SQL SKRIPT AUSFÜHREN ##########
def execute_statements(sql_script):
    #init DB Connection
    server = "itxchdm.switzerlandnorth.cloudapp.azure.com"
    database = "NGDWA"
    username = "chdm"
    password = "IT-Logix32"
    conn = pyodbc.connect("DRIVER={SQL Server};SERVER="+server+";DATABASE="+database+";UID="+username+";PWD="+ password)

    if doExecute:

        # Template SQL Ausführung
        #sql = "select count(*) cnt from dwh.dim_Patient"
        #cursor = conn.cursor()
        #result = pd.read_sql_query(sql, conn)
        #cnt = int(result.cnt[0])
        #print("count: " + str(cnt))
        #cursor.close()
    
        #cursor = conn.cursor()
        #cursor.execute(script)
        with conn.cursor() as cursor:
            for statement in sql_script.split(";"):
                print(statement)
                if len(statement) > 0:
                    cursor.execute(statement)
                    conn.commit()
        cursor.close()
    else:
        print('--- SQL Script ------------------------------------------------')
        print(sql_script)
        print('---------------------------------------------------------------')

def get_dummy_value_per_datatype(datatype, column_name, mandatory):
    if mandatory == "null":
        dummy_value = "NULL"
    elif "_bk" in column_name or column_name == "InternalId":
        dummy_value = "'-1'"
    elif "varchar" in datatype:
        length = int(datatype.split("(")[1].split(")")[0])
        if length <= 5:
            dummy_value = "'-'"
        else:
            dummy_value = "'#NA#'"
    elif "number" in datatype or "integer" in datatype or "int" in datatype or "decimal" in datatype or "float" in datatype or "real" in datatype:
        dummy_value = "0"
    elif "datetime" in datatype and ("from" in column_name or "since" in column_name or "insert" in column_name or "update" in column_name):
        dummy_value = "'1900-01-01 00:00:00'"
    elif "datetime" in datatype and ("to" in column_name or "until" in column_name):
        dummy_value = "'9999-12-31 23:59:59'"
    elif "datetime" in datatype:
        dummy_value = "'9999-12-31 23:59:59'"
    elif datatype == "date" and ("from" in column_name or "since" in column_name or "insert" in column_name or "update" in column_name):
        dummy_value = "'1900-01-01'"
    elif datatype == "date" and ("to" in column_name or "until" in column_name):
        dummy_value = "'9999-12-31'"
    elif datatype == "date":
        dummy_value = "'9999-12-31'"
    elif datatype == "time":
        dummy_value = "'00:00:00'"
    elif datatype == "boolean":
        dummy_value = "false"

    return dummy_value

def setStandardDefaults(p_tabledef):
    #in der Tabellendefinition Standarddefaults einsetzen. Falls "default" <> "" wird nichts gemacht!
    v_tabledef = p_tabledef
    i = 0
    for feld in v_tabledef["columns"]:        
        if feld["default"] == "":
            v_default = get_dummy_value_per_datatype(feld["data_type"], feld["column_name"], feld["mandatory"])
            v_tabledef["columns"][i]["default"] = v_default
        i += 1    
    return v_tabledef


########## STA 90er VIEW ERSTELLEN ##########
def sta_90er_view(schema_name, table_name, bk_column, column_list):
    # STA-90er VIEW
    # Init Script Variable
    view_name = schema_name + ".v_" + table_name + "_90"
    script = ""
    ## STA-90er VIEW: SCRIPT HEADER
    script_view_header = "begin\n	declare @view_exists int\n	declare @sql nvarchar(max)\n	select @view_exists = 1 from sysobjects where id = object_id('" + view_name + "') and type = 'V'\n	if @view_exists is null\n       begin\n             SET @sql = '"
    script = script + script_view_header
    if printInfo:
        print(script)
    ## STA-90er VIEW: View Header ##
    script_view_header = "create view " + view_name + " as\nselect\n"
    script = script + script_view_header
    if printInfo:
        print(script)
    ## STA-90er VIEW: BK COLUMN ##
    script_bk_column = bk_column.iloc[0,0] + " = CAST(NULL as " + bk_column.iloc[0,1] + ")\n"
    script = script + script_bk_column
    if printInfo:
        print(script)
    ## STA-90er VIEW: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "," + column_list.iloc[i, 0] + " = CAST(NULL as " + column_list.iloc[i, 1] + ")\n"
        i=i+1
        script = script + script_column_list
    if printInfo:
        print(script)
    ## STA-90er VIEW: Footer ##
    script_view_footer = "where 1=2\n'\n			exec sp_executesql @sql\n		end\nend"
    script = script + script_view_footer
    if printInfo:
        print(script)
    execute_statements(script)


def sta_90er_view_PLAN_B(schema_name, p_src_table):    
    # kleiner Vorteil neben Lesbarkeit: die Templates lassen sich auch in Files oder Datenbanktabellen halten. ;-)

    tmplSQL = """
begin
    declare @view_exists int
    declare @sql nvarchar(max)
    select @view_exists = 1 from sysobjects where id = object_id('{{v_view_name}}_90') and type = 'V'
    if @view_exists is null
    begin
        SET @sql = 'create view {{v_view_name}}_90 as
        select
            {%- for feld in v_column_list %}
            {{ ", " if not loop.first else "" }}{{feld["column_name"]}} = CAST(NULL as {{feld["data_type"]}})
            {%- endfor %}
        from xyz
        where 1=1
        '
        exec sp_executesql @sql
    end
end
"""
    
    view_name = schema_name + ".v_" + p_src_table["table_name"]

    environment = jinja2.Environment()
    template = environment.from_string(tmplSQL)
    script = template.render(v_view_name=view_name, v_column_list=p_src_table["columns"])
    
    execute_statements(script)
    
    
########## STA 91er VIEW ERSTELLEN ##########
def sta_91er_view(schema_name, table_name, bk_column, column_list):
    # STA-91er VIEW
    # Init Script Variable
    view_name = schema_name + ".v_" + table_name + "_91"
    script = ""
    ## STA-91er: DROP TABLE
    script_drop_view = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + view_name + "')\n and type = 'V')\n drop view " + view_name + " \n;\n"
    script = script + script_drop_view
    if printInfo:
        print(script)
    ## STA-91er VIEW: View Header ##
    script_view_header = "create view " + view_name + " as\nselect\n"
    script = script + script_view_header
    if printInfo:
        print(script)
    ## STA-91er VIEW: BK COLUMN ##
    script_bk_column = bk_column.iloc[0,0] + " = isnull(" + bk_column.iloc[0,0] + ",'-1')\n"
    script = script + script_bk_column
    if printInfo:
        print(script)
    ## STA-91er VIEW: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "  ," + column_list.iloc[i, 0] + "                   = isnull(" + column_list.iloc[i, 0] + "," + get_dummy_value_per_datatype(column_list.iloc[i, 1], column_list.iloc[i, 0], column_list.iloc[i, 2]) + ")\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "  ,dim_Date_" + column_list.iloc[i, 0] + "_bk                   = isnull(CAST(" + column_list.iloc[i, 0] + " as date)," + get_dummy_value_per_datatype(column_list.iloc[i, 1], column_list.iloc[i, 0], column_list.iloc[i, 2]) + ")\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "  ,dim_Time_" + column_list.iloc[i, 0] + "_bk                   = isnull(CAST(" + column_list.iloc[i, 0] + " as time)," + get_dummy_value_per_datatype(column_list.iloc[i, 1], column_list.iloc[i, 0], column_list.iloc[i, 2]) + ")\n"
        i=i+1
        script = script + script_column_list
    if printInfo:
        print(script)
    ## STA-91er VIEW: Footer ##
    script_view_footer = "from " + view_name.replace("_91", "_90")
    script = script + script_view_footer
    if printInfo:
        print(script)
    execute_statements(script)

def sta_91er_view_PLAN_B(schema_name, p_src_table):
    
    tmplSQL = """
if exists (select 1 
from  sysobjects 
where id = object_id('{{v_view_name}}_91')
    and type = 'V')
drop view {{v_view_name}}_91 
;
create view {{v_view_name}}_91 as
select
    {%- for feld in v_column_list %}
    {{ ", " if not loop.first else "" }}{{feld["column_name"]}} = isnull({{feld["column_name"]}}, {{feld["default"]}}) 
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    , dim_Date_{{feld["column_name"]}}_bk = isnull(CAST({{feld["column_name"]}} as date), {{feld["default"]}})
    {%- endif %}
    {%- if data_type == 'datetime' %}
    , dim_Time_{{feld["column_name"]}}_bk = isnull(CAST({{feld["column_name"]}} as time), {{feld["default"]}})
    {%- endif %}
    {%- endfor %}
from {{v_view_name}}_90
where 1=1
"""

    view_name = schema_name + ".v_" + p_src_table["table_name"] 

    environment = jinja2.Environment()
    template = environment.from_string(tmplSQL)
    script = template.render(v_view_name=view_name, v_column_list=p_src_table["columns"])
    
    execute_statements(script)

########## STA TABELLE ERSTELLEN ##########
def sta_table(schema_name, table_name, bk_column, column_list):
    # STA-TABLE
    # Init Script Variable
    script = ""
    table_schema_name = schema_name + "." + table_name
    ## STA-TABLE: DROP TABLE
    script_drop_sta_table = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + table_schema_name + "')\n and type = 'U')\n drop table " + table_schema_name + " \n;\n"
    script = script + script_drop_sta_table
    print(script)
    ## STA-TABLE: TABLE HEADER AND BATCH_RUN_ID ##
    script_table_header = "create table " + table_schema_name + " (\n"
    script = script + script_table_header
    print(script)
    ## STA-TABLE: BK COLUMN ##
    script_bk_column = bk_column.iloc[0,0] + " " + bk_column.iloc[0,1] + " " + bk_column.iloc[0,2] + ",\n"
    script = script + script_bk_column
    print(script)
    ## STA-TABLE: DWH META COLUMNS ##
    script_meta_column = "dwh_BatchRunIdInsert integer NOT NULL,\n" \
                         "dwh_DeleteFlag integer not null,\n"
    script = script + script_meta_column
    print(script)
    ## STA-TABLE: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = column_list.iloc[i, 0] + " " + column_list.iloc[i, 1] + " " + column_list.iloc[i, 2] + ",\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "dim_Date_" + column_list.iloc[i, 0] + "_bk nvarchar(10) " + column_list.iloc[i, 2] + ",\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "dim_Time_" + column_list.iloc[i, 0] + "_bk nvarchar(8) " + column_list.iloc[i, 2] + ",\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## STA-TABLE: PK ##
    script_pk_constraint = "constraint " + table_name + "_pk primary key (" + bk_column.iloc[0,0] + ")\n)\n;\n"
    script = script + script_pk_constraint
    print(script)
    execute_statements(script)


def sta_table_PLAN_B(schema_name, p_src_table):
    tmplSQL = """
{%- set ns = namespace(has_pk=0) -%}
if exists (select 1 
    from sysobjects 
    where id = object_id('{{v_table_schema_name}}')
        and type = 'U')
drop table {{v_table_schema_name}}
;
create table {{v_table_schema_name}} (
    dwh_BatchRunIdInsert integer NOT NULL,
    dwh_DeleteFlag integer not null,
    {%- for feld in v_column_list %}
    {%- if feld["pk"] == 1 %} {%- set ns.has_pk = 1 -%} {%- endif %}
    {{feld["column_name"]}} {{feld["data_type"]}} {{feld["mandatory"]}}{{ ", " if not loop.last else "" }}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    dim_Date_{{feld["column_name"]}}_bk nvarchar(10) {{feld["mandatory"]}}{{ ", " if not loop.last else "" }}
    {%- endif %}
    {%- if data_type == 'datetime' %}
    dim_Time_{{feld["column_name"]}}_bk nvarchar(8) {{feld["mandatory"]}}{{ ", " if not loop.last else "" }}
    {%- endif %}
    {%- endfor -%}
    {# constraints  #}
    {%- if ns.has_pk == 1 %}
    , constraint 
    {%- endif %}
    
    dim_Patient_bk nvarchar(56) not null,
    dwh_BatchRunIdInsert integer NOT NULL,
    dwh_DeleteFlag integer not null,
    dim_SourceSystem_bk nvarchar(5) not null,
    InternalId nvarchar(50) not null,
    FirstName nvarchar(255) not null,
    LastName nvarchar(255) not null,
    BirthDate datetime null,
    dim_Date_BirthDate_bk nvarchar(10) null,
    dim_Time_BirthDate_bk nvarchar(8) null,
    dim_Country_ResidenceCountry_bk nvarchar(5) not null,
    dim_Country_BirthCountry_bk nvarchar(5) not null,
    dim_Country_CitizenshipCountry_bk nvarchar(5) not null,
    GestationalAgeInDays integer null,
    constraint dim_Patient_pk primary key (dim_Patient_bk)
)
"""
    table_schema_name = schema_name + "." + p_src_table["table_name"]
    
    environment = jinja2.Environment()
    template = environment.from_string(tmplSQL)
    script = template.render(v_table_schema_name=table_schema_name, v_column_list=p_src_table["columns"])
    
    execute_statements(script)
    
    
########## DWH TABELLE ERSTELLEN ##########
def dwh_table(schema_name, table_name, bk_column, column_list):
    # DWH-TABLE
    # Init Script Variable
    script = ""
    table_schema_name = schema_name + "." + table_name
    current_time = dt.now().strftime('%Y%m%d_%H%M%S')
    ## DWH-TABLE: RENAME TABLE
    script_rename_dwh_table = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + table_schema_name + "')\n and type = 'U')\n exec sp_rename '" + table_schema_name + "', 'xxx_" + table_name + "_" + current_time + "';\nexec sp_rename '" + table_schema_name + "_pk', 'xxx_" + table_name + "_pk_" + current_time + "';\n;\n"
    script = script + script_rename_dwh_table
    print(script)
    ## DWH-TABLE: TABLE HEADER AND BATCH_RUN_ID ##
    script_table_header = "create table " + table_schema_name + " (\n"
    script = script + script_table_header
    print(script)
    ## DWH-TABLE: SID COLUMN ##
    script_sid_column = table_name + "_sid integer not null,\n"
    script = script + script_sid_column
    print(script)
    ## DWH-TABLE: BK COLUMN ##
    script_bk_column = bk_column.iloc[0,0] + " " + bk_column.iloc[0,1] + " " + bk_column.iloc[0,2] + ",\n"
    script = script + script_bk_column
    print(script)
    ## DWH-TABLE: DWH META COLUMNS ##
    script_meta_column = "dwh_ValidFrom datetime NOT NULL,\n" \
                         "dwh_ValidTo datetime NOT NULL,\n" \
                         "dwh_CurrentFlag integer NOT NULL,\n" \
                         "dwh_DeleteFlag integer NOT NULL,\n" \
                         "dwh_EarlyArriveFlag integer NOT NULL,\n" \
                         "dwh_EarlyArriveField nvarchar(255) NOT NULL,\n" \
                         "dwh_InsertDate datetime NOT NULL\n," \
                         "dwh_UpdateDate datetime NULL,\n" \
                         "dwh_BatchRunIdInsert integer NOT NULL,\n" \
                         "dwh_BatchRunIdUpdate integer NOT NULL,\n"
    script = script + script_meta_column
    print(script)
    ## DWH-TABLE: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = column_list.iloc[i, 0] + " " + column_list.iloc[i, 1] + " " + column_list.iloc[i, 2]+ ",\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "dim_Date_" + column_list.iloc[i, 0] + "_bk nvarchar(10) " + column_list.iloc[i, 2] + ",\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "dim_Time_" + column_list.iloc[i, 0] + "_bk nvarchar(8) " + column_list.iloc[i, 2] + ",\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## DWH-TABLE: PK ##
    script_pk_constraint = "constraint " + table_name + "_pk primary key (" + table_name + "_sid)\n)\n;\n"
    script = script + script_pk_constraint
    print(script)
    execute_statements(script)

########## DWH TABELLE ERSTELLEN ##########
def rep_views(schema_name, table_name, bk_column, column_list):
    # REP-VIEWS
    # Init Script Variable
    script = ""
    view_name = schema_name + ".v_" + table_name
    view_name_cur = view_name + "_cur"
    view_name_cid = view_name + "_cid"
    view_name_fhi = view_name + "_fhi"
    ## REP-VIEWS: DROP REP-VIEWS
    script_drop_rep_views = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + view_name_cur +"')\n and type = 'V')\n drop view " + view_name_cur +" \n;\n"
    script = script + script_drop_rep_views
    script_drop_rep_views = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + view_name_cid +"')\n and type = 'V')\n drop view " + view_name_cid +" \n;\n"
    script = script + script_drop_rep_views
    script_drop_rep_views = "if exists (select 1 \nfrom  sysobjects where id = object_id('" + view_name_fhi +"')\n and type = 'V')\n drop view " + view_name_fhi +" \n;\n"
    script = script + script_drop_rep_views
    print(script)
    ## REP-VIEWS: TABLE HEADER AND BATCH_RUN_ID ##
    script_view_header = "create view " + view_name_fhi + " as\nselect\n"
    script = script + script_view_header
    print(script)
    ## REP-VIEWS: SID COLUMN ##
    script_sid_column = table_name + "_sid\n"
    script = script + script_sid_column
    print(script)
    ## REP-VIEWS: BK COLUMN ##
    script_bk_column = "," + bk_column.iloc[0,0] + "\n"
    script = script + script_bk_column
    print(script)
    ## REP-VIEWS: DWH META COLUMNS ##
    script_meta_column = ",dwh_ValidFrom\n" \
                         ",dwh_ValidTo\n" \
                         ",dwh_CurrentFlag\n" \
                         ",dwh_DeleteFlag\n" \
                         ",dwh_EarlyArriveFlag\n" \
                         ",dwh_EarlyArriveField\n" \
                         ",dwh_InsertDate\n" \
                         ",dwh_UpdateDate\n" \
                         ",dwh_BatchRunIdInsert\n" \
                         ",dwh_BatchRunIdUpdate\n"
    script = script + script_meta_column
    print(script)
    ## REP-VIEWS: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "," + column_list.iloc[i, 0] + "\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + ",dim_Date_" + column_list.iloc[i, 0] + "_bk\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + ",dim_Time_" + column_list.iloc[i, 0] + "_bk\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## REP-VIEWS: PK ##
    ## REP-VIEWS: Footer ##
    script_view_footer = "from dwh." + table_name # --> TODO: dwh. hard coded...
    script = script + script_view_footer
    print(script)
    execute_statements(script)
    # REP-VIEWS: cur-View
    script = script.replace(view_name_fhi,view_name_cid)
    script = script + "\nwhere dwh_CurrentFlag = 1"
    print(script)
    execute_statements(script)
    # REP-VIEWS: cur-View
    script = script.replace(view_name_cid,view_name_cur)
    script = script + "\nand dwh_DeleteFlag = 0\nand dwh_EarlyArriveFlag = 0"
    print(script)
    execute_statements(script)

def proc_sta_dummy(schema_name, table_name, bk_column, column_list):
    # STA DUMMY PROCEDURE
    # Init Script Variable
    proc_name = schema_name + ".usp_" + table_name +"_dummy"
    print(proc_name)
    script = ""
    ## STA DUMMY PROCEDURE: DROP PROCEDURE
    script_drop_proc = "if exists (select 1 \nfrom sysobjects where id = object_id('" + proc_name + "')\n and type = 'P')\n drop procedure " + proc_name + " \n;\n"
    script = script + script_drop_proc
    print(script)
    ## STA DUMMY PROCEDURE: PROCEDURE HEADER ##
    script_proc_header = "create procedure " + proc_name + " \n  @BatchRunIdInsert int\nas\nbegin\n insert into " + schema_name + "." + table_name + "\n select\n"
    script = script + script_proc_header
    print(script)
    ## STA DUMMY PROCEDURE: BK COLUMN ##
    script_bk_column = "   " + bk_column.iloc[0, 0] + "           = '-1'\n"
    script = script + script_bk_column
    print(script)
    ## STA DUMMY PROCEDURE: STA META COLUMNS ##
    script_meta_column = "  ,dwh_BatchRunIdInsert     = @BatchRunIdInsert\n" \
                         "  ,dwh_DeleteFlag           = 0\n"
    script = script + script_meta_column
    print(script)
    ## STA DUMMY PROCEDURE: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "  ," + column_list.iloc[i, 0] + "                   = " + get_dummy_value_per_datatype(column_list.iloc[i, 1], column_list.iloc[i, 0], column_list.iloc[i, 2]) + "\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "  ,dim_Date_" + column_list.iloc[i, 0] + "_bk                   = '-1'\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "  ,dim_Time_" + column_list.iloc[i, 0] + "_bk                   = '-1'\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## STA DUMMY PROCEDURE: PROCEDURE FOOTER ##
    script_proc_footer = "end\n;\n"
    script = script + script_proc_footer
    print(script)
    execute_statements(script)

def proc_sta_full_load(schema_name, table_name, bk_column, column_list):
    # STA FULL LOAD PROCEDURE
    # Init Script Variable
    proc_name = schema_name + ".usp_" + table_name +"_full_load"
    print(proc_name)
    view_name = schema_name + ".v_" + table_name + "_91"
    sta_table_name = schema_name + "." + table_name
    print(view_name)
    script = ""
    ## STA FULL LOAD PROCEDURE: DROP PROCEDURE
    script_drop_proc = "if exists (select 1 \nfrom sysobjects where id = object_id('" + proc_name + "')\n and type = 'P')\n drop procedure " + proc_name + " \n;\n"
    script = script + script_drop_proc
    print(script)
    ## STA FULL LOAD PROCEDURE: PROCEDURE HEADER ##
    script_proc_header = "create procedure " + proc_name + " \n  @BatchRunIdInsert int\nas\nbegin\n truncate table " + sta_table_name + "\n\n  insert into " + sta_table_name + "\n select\n"
    script = script + script_proc_header
    print(script)
    ## STA FULL LOAD PROCEDURE: BK COLUMN ##
    script_bk_column = "   " + bk_column.iloc[0, 0] + "\n"
    script = script + script_bk_column
    print(script)
    ## STA FULL LOAD PROCEDURE: STA META COLUMNS ##
    script_meta_column = "  ,dwh_BatchRunIdInsert     = @BatchRunIdInsert\n" \
                         "  ,dwh_DeleteFlag           = 0\n"
    script = script + script_meta_column
    print(script)
    ## STA FULL LOAD PROCEDURE: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "  ," + column_list.iloc[i, 0] + "\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "  ,dim_Date_" + column_list.iloc[i, 0] + "_bk                   = convert(nvarchar(10), " + column_list.iloc[i, 0] + ", 120)\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "  ,dim_Time_" + column_list.iloc[i, 0] + "_bk                   = convert(nvarchar(8), " + column_list.iloc[i, 0] + ", 14)\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## STA FULL LOAD PROCEDURE: PROCEDURE FOOTER ##
    script_proc_footer = "  from " + view_name + "\nend\n;\n"
    script = script + script_proc_footer
    print(script)
    execute_statements(script)

def proc_sta_delete_detection(schema_name, table_name, bk_column, column_list):
    # STA DELETE DETECTION
    # Init Script Variable
    proc_name = schema_name + ".usp_" + table_name +"_delete_detection"
    print(proc_name)
    dwh_table_name = "dwh." + table_name               # --> TODO: hard coded...
    sta_table_name = schema_name + "." + table_name
    script = ""
    ## STA DELETE DETECTION PROCEDURE: DROP PROCEDURE
    script_drop_proc = "if exists (select 1 \nfrom sysobjects where id = object_id('" + proc_name + "')\n and type = 'P')\n drop procedure " + proc_name + " \n;\n"
    script = script + script_drop_proc
    print(script)
    ## STA DELETE DETECTION PROCEDURE: PROCEDURE HEADER ##
    script_proc_header = "create procedure " + proc_name + " \n  @BatchRunIdInsert int\nas\nbegin\n\n  insert into " + sta_table_name + "\n select\n"
    script = script + script_proc_header
    print(script)
    ## STA DELETE DETECTION PROCEDURE: BK COLUMN ##
    script_bk_column = "   " + bk_column.iloc[0, 0] + "\n"
    script = script + script_bk_column
    print(script)
    ## STA DELETE DETECTION PROCEDURE: STA META COLUMNS ##
    script_meta_column = "  ,dwh_BatchRunIdInsert     = @BatchRunIdInsert\n" \
                         "  ,dwh_DeleteFlag           = 1\n"
    script = script + script_meta_column
    print(script)
    ## STA DELETE DETECTION PROCEDURE: COLUMN_LIST ##
    i = 0
    while i < len(column_list):
        script_column_list = "  ," + column_list.iloc[i, 0] + "\n"
        if column_list.iloc[i, 1] == 'datetime' or column_list.iloc[i, 1] == 'date':
            script_column_list = script_column_list + "  ,dim_Date_" + column_list.iloc[i, 0] + "_bk\n"
        if column_list.iloc[i, 1] == 'datetime':
            script_column_list = script_column_list + "  ,dim_Time_" + column_list.iloc[i, 0] + "_bk\n"
        i=i+1
        script = script + script_column_list
    print(script)
    ## STA DELETE DETECTION PROCEDURE: PROCEDURE FOOTER ##
    script_proc_footer = "  from " + dwh_table_name + " dwh\n   where dwh_DeleteFlag = 0\nand not exists (\n        select *\nfrom " + sta_table_name + " stg\n     where stg." + bk_column.iloc[0, 0] + " = dwh." + bk_column.iloc[0, 0] + "\n     )\nend\n;\n"
    script = script + script_proc_footer
    print(script)
    execute_statements(script)

####################### MAIN EXECUTION ###############################

src_table = setStandardDefaults(src_table)
if printInfo:
    print (src_table)

#sta_90er_view(sta_schema_name, table_name, bk_column, column_list)
#sta_90er_view_PLAN_B(sta_schema_name, src_table)

#sta_91er_view(sta_schema_name, table_name, bk_column, column_list)
#sta_91er_view_PLAN_B(sta_schema_name, src_table)

sta_table(sta_schema_name, table_name, bk_column, column_list)
sta_table_PLAN_B(sta_schema_name, src_table)

#dwh_table(dwh_schema_name, table_name, bk_column, column_list)

#rep_views(rep_schema_name, table_name, bk_column, column_list)

#proc_sta_dummy(sta_schema_name, table_name, bk_column, column_list)

#proc_sta_full_load(sta_schema_name, table_name, bk_column, column_list)

#proc_sta_delete_detection(sta_schema_name, table_name, bk_column, column_list)

