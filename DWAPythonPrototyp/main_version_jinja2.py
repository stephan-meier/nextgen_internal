import pyodbc
from datetime import datetime as dt
import jinja2

doExecute = False
printInfo = False

# TODO: als Konfig File auslagern
sta_schema_name = "stg"
dwh_schema_name = "dwh"
rep_schema_name = "rep"


######## Diese Informationen müssen vom Interface des Modellierungstools eingelesen werden - START ######

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
            'pk': 1,
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

tmpl_sta_90er_view_SQL = """
begin
    declare @view_exists int
    declare @sql nvarchar(max)
    select @view_exists = 1 from sysobjects where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_90') and type = 'V'
    if @view_exists is null
    begin
        SET @sql = 'create view {{v_schema_name}}.v_{{v_src_table.table_name}}_90 as
        select
            {%- for feld in v_src_table.columns %}
            {{ ", " if not loop.first else "" }}{{feld["column_name"]}} = CAST(NULL as {{feld["data_type"]}})
            {%- endfor %}
        from xyz
        where 1=1
        '
        exec sp_executesql @sql
    end
end
"""

tmpl_sta_91er_view_SQL = """
if exists (select 1 
from  sysobjects 
where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_91')
    and type = 'V')
drop view {{v_schema_name}}.v_{{v_src_table.table_name}}_91
;

create view {{v_schema_name}}.v_{{v_src_table.table_name}}_91 as
select
    {%- for feld in v_src_table.columns %}
    {{ ", " if not loop.first else "" }}{{feld["column_name"]}} = isnull({{feld["column_name"]}}, {{feld["default"]}}) 
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    , dim_Date_{{feld["column_name"]}}_bk = isnull(CAST({{feld["column_name"]}} as date), {{feld["default"]}})
    {%- endif %}
    {%- if data_type == 'datetime' %}
    , dim_Time_{{feld["column_name"]}}_bk = isnull(CAST({{feld["column_name"]}} as time), {{feld["default"]}})
    {%- endif %}
    {%- endfor %}
from {{v_schema_name}}.v_{{v_src_table.table_name}}_90
where 1=1
"""

tmpl_sta_table_SQL = """
{%- set ns = namespace(has_pk=0) -%}
if exists (select 1 
    from sysobjects 
    where id = object_id('{{v_schema_name}}.{{v_src_table.table_name}}')
        and type = 'U')
drop table {{v_schema_name}}.{{v_src_table.table_name}}
;
create table {{v_schema_name}}.{{v_src_table.table_name}} (
    dwh_BatchRunIdInsert integer NOT NULL,
    dwh_DeleteFlag integer not null,
    {%- for feld in v_src_table.columns %}
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
    ,constraint {{v_src_table.pk_name}} primary key (
    {%- for feld in v_src_table.columns -%}
    {%- if feld["pk"] == 1 -%} 
    {{ ", " if not loop.first else "" }}{{feld["column_name"]}}
    {%- endif -%}
    {%- endfor -%})
    {%- endif %}
)
"""

tmpl_dwh_table_SQL = """
{%- set ns = namespace(has_pk=0) -%}
if exists (select 1 
from  sysobjects where id = object_id('{{v_schema_name}}.{{v_src_table.table_name}}')
 and type = 'U')
exec sp_rename '{{v_schema_name}}.{{v_src_table.table_name}}', 'xxx_{{v_src_table.table_name}}_{{v_ts}}';
exec sp_rename '{{v_schema_name}}.{{v_src_table.table_name}}_pk', 'xxx_{{v_src_table.table_name}}_pk_{{v_ts}}';
;
create table {{v_schema_name}}.{{v_src_table.table_name}} (
    dwh_ValidFrom datetime NOT NULL,
    dwh_ValidTo datetime NOT NULL,
    dwh_CurrentFlag integer NOT NULL,
    dwh_DeleteFlag integer NOT NULL,
    dwh_EarlyArriveFlag integer NOT NULL,
    dwh_EarlyArriveField nvarchar(255) NOT NULL,
    dwh_InsertDate datetime NOT NULL,
    dwh_UpdateDate datetime NULL,
    dwh_BatchRunIdInsert integer NOT NULL,
    dwh_BatchRunIdUpdate integer NOT NULL,
    {{v_src_table.table_name}}_sid integer not null,
    {%- for feld in v_src_table.columns %}
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
    {# mandatory constraint SID  #}
    , constraint {{v_src_table.table_name}}_pk primary key ({{v_src_table.table_name}}_sid)
)
;
"""

tmpl_rep_views_SQL = """
if exists (select 1 
from  sysobjects where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_cur')
 and type = 'V')
 drop view {{v_schema_name}}.v_{{v_src_table.table_name}}_cur
;

create view {{v_schema_name}}.v_{{v_src_table.table_name}}_cur as
select
    dwh_ValidFrom
    ,dwh_ValidTo
    ,dwh_CurrentFlag
    ,dwh_DeleteFlag
    ,dwh_EarlyArriveFlag
    ,dwh_EarlyArriveField
    ,dwh_InsertDate
    ,dwh_UpdateDate
    ,dwh_BatchRunIdInsert
    ,dwh_BatchRunIdUpdate
    ,{{v_src_table.table_name}}_sid
    {%- for feld in v_src_table.columns %}
    ,{{feld["column_name"]}} 
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk
    {%- endif %}    
    {%- endfor %}
from dwh.{{v_src_table.table_name}}
where 1=1
    and dwh_CurrentFlag = 1
    and dwh_DeleteFlag = 0
    and dwh_EarlyArriveFlag = 0    
"""

tmpl_proc_sta_dummy_SQL = """
if exists (select 1 

from sysobjects where id = object_id('{{v_schema_name}}.usp_{{v_src_table.table_name}}_dummy')
 and type = 'P')
 drop procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_dummy
;
create procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_dummy
  @BatchRunIdInsert int
as
begin
  insert into {{v_schema_name}}.{{v_src_table.table_name}}
  select
    dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 0
    {%- for feld in v_src_table.columns %}
    ,{{feld["column_name"]}} = {{feld["default"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk = '-1'
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk = '-1'
    {%- endif %}    
    {%- endfor %}    
end
;
"""

tmpl_proc_sta_full_load_SQL = """
if exists (select 1 
  from sysobjects where id = object_id('{{v_schema_name}}.usp_{{v_src_table.table_name}}_full_load')
  and type = 'P')
drop procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_full_load
;
create procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_full_load
  @BatchRunIdInsert int
as
begin
  truncate table {{v_schema_name}}.{{v_src_table.table_name}}

  insert into {{v_schema_name}}.{{v_src_table.table_name}}
  select
    dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 0
    {%- for feld in v_src_table.columns %}
    ,{{feld["column_name"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk = convert(nvarchar(10), {{feld["column_name"]}}, 120)
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk = convert(nvarchar(8), {{feld["column_name"]}}, 14)
    {%- endif %}    
    {%- endfor %}
  from {{v_schema_name}}.v_{{v_src_table.table_name}}_91
end
;
"""

tmpl_proc_sta_delete_detection_SQL = """
{# bk suchen, das letzte Feld mit bk Flag wird genommen! #}
{%- set ns = namespace(bk_name='') -%}
{%- for feld in v_src_table.columns -%}
{%- if feld["bk"] == 1 %} {%- set ns.bk_name = feld["column_name"] -%} {%- endif %}
{%- endfor -%})

if exists (select 1 
from sysobjects where id = object_id('{{v_schema_name}}.usp_{{v_src_table.table_name}}_delete_detection')
  and type = 'P')
drop procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_delete_detection
;
create procedure {{v_schema_name}}.usp_{{v_src_table.table_name}}_delete_detection
  @BatchRunIdInsert int
as
begin
  insert into {{v_schema_name}}.{{v_src_table.table_name}}
  select
    dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 1
    {%- for feld in v_src_table.columns %}
    ,{{feld["column_name"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk
    {%- endif %}    
    {%- endfor %}   
  from dwh.{{v_src_table.table_name}} dwh
    where 1=1 
    and dwh_DeleteFlag = 0
    and not exists (
        select *
        from {{v_schema_name}}.{{v_src_table.table_name}} stg
        where {{v_schema_name}}.{{ns.bk_name}} = dwh.{{ns.bk_name}}
    )
end
;
"""


job_pipeline = (
('sta_90er_view',             sta_schema_name, tmpl_sta_90er_view_SQL),
('sta_91er_view',             sta_schema_name, tmpl_sta_91er_view_SQL),
('sta_table',                 sta_schema_name, tmpl_sta_table_SQL),
('dwh_table',                 dwh_schema_name, tmpl_dwh_table_SQL),
('rep_views',                 rep_schema_name, tmpl_rep_views_SQL),
('proc_sta_dummy',            sta_schema_name, tmpl_proc_sta_dummy_SQL),
('proc_sta_full_load',        sta_schema_name, tmpl_proc_sta_full_load_SQL),
('proc_sta_delete_detection', sta_schema_name, tmpl_proc_sta_delete_detection_SQL)
)



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



def build_query(template, schema_name, p_src_table, p_ts):    
    script = ''
    environment = jinja2.Environment()
    template = environment.from_string(template)
    script = template.render(v_schema_name=schema_name, v_src_table=p_src_table, v_ts=p_ts)
    return(script)
    


####################### MAIN EXECUTION ###############################

# Defaults in der Tabelle ergänzen
src_table = setStandardDefaults(src_table)
if printInfo:
    print (src_table)
    
# einen Timestamp für die Pipeline generieren
jetzt = dt.now()
jetztString = jetzt.strftime("%Y%m%d%H%M%S")
if printInfo:
    print (jetztString)

# Queries generieren (und ausführen)
for job in job_pipeline:
    print(job[0])
    sql = build_query(job[2], job[1], src_table, jetztString)
    execute_statements(sql)

