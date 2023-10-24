"""
Package files mit templates, ablauf und schemas.
Package info in tabelle.  Fileauswahl in Tabelle ('dim_*'), '' oder '*' gilt für alle. Oder Fileparameter.
Verzeichnis aufruf, kein package: kein code.
Oder verzechnisaufruf mit 'dim_' und packagename, der die packageinfo übersteuert. Verzeichnis '*' alle mit tudätzlichem package +bsp. Drop table template

Protect flag!!
Embedded, override oder default transformation
Embedded, falls leer passiert nichts
Default, falls eintrag, dann der sonst default transformation
Override, eine über alles, bzw. Die selektion

Protected flag schützt immer

Allowed_mode
In template package, zeigt, wo das template eingesetzt werden darf.
Bsp drop erlaubt nur mode override, alles andere (default, lerr) wird übersteuert.

plus sqlalchemy um unabhängiger zur Datenbnk zu sein (speziell Metadaten holen, sources für PSA generieren)

"""

from datetime import datetime as dt
import logging
import os
import time
import datetime
import json
import sys

import pyodbc
import jinja2
import yaml
from yaml.loader import SafeLoader


#sys.path.insert(1, 'C:/Users/steph/Downloads/lib')

from lib.dirmgmt import getSubdirs, getFiles

doExecute = False
printInfo = False

logging_file = './gen.log'
tasks_name = 'tasks.yml'     # das YAML File mit den Task Definitionen, muss in jeder Template Grupppe vorhanden sein!

source_dir = './source/'
template_dir = './templates/'
run_templates = 'core'


# Defaultwerte, dir richtigen Werte kommen aus dem tasks.yml File
sta_schema_name = "default_stg"
dwh_schema_name = "default_dwh"
rep_schema_name = "default_rep"


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


#---------------------------------------------------------------
# Code Templates
#---------------------------------------------------------------

tmpl_sta_90er_view_SQL = """
begin
    declare @view_exists int
    declare @sql nvarchar(max)
    select @view_exists = 1 from sysobjects where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_90') and type = 'V'
    if @view_exists is NULL
    begin
        SET @sql = 'create view {{v_schema_name}}.v_{{v_src_table.table_name}}_90 as
        select
            {%- for feld in v_src_table.columns %}
            {{ "," if not loop.first else " " }}{{feld["column_name"]}} = CAST(NULL as {{feld["data_type"]}})
            {%- endfor %}
        where 1=2
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
    {{ "," if not loop.first else " " }}{{feld["column_name"]}} = isNULL({{feld["column_name"]}}, {{feld["default"]}}) 
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    , dim_Date_{{feld["column_name"]}}_bk = isNULL(CAST({{feld["column_name"]}} as date), {{feld["default"]}})
    {%- endif %}
    {%- if data_type == 'datetime' %}
    , dim_Time_{{feld["column_name"]}}_bk = isNULL(CAST({{feld["column_name"]}} as time), {{feld["default"]}})
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
    {%- for feld in v_src_table.columns %}
    {%- if feld["pk"] == 1 %} {%- set ns.has_pk = 1 -%} {%- endif %}
    {{ "," if not loop.first else " " }}{{feld["column_name"]}} {{feld["data_type"]}} {{feld["mandatory"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk nvarchar(10) {{feld["mandatory"]}}
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk nvarchar(8) {{feld["mandatory"]}}
    {%- endif %}
    {%- endfor -%}
    {# Standard fields  #}
    ,dwh_BatchRunIdInsert integer NOT NULL
    ,dwh_DeleteFlag integer NOT NULL
    {# constraints  #}
    {%- if ns.has_pk == 1 %}
    ,constraint {{v_src_table.pk_name}} primary key (
    {%- for feld in v_src_table.columns -%}
    {%- if feld["pk"] == 1 -%} 
    {{ "," if not loop.first else " " }}{{feld["column_name"]}}
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
 begin
  print('exists')
  exec sp_rename '{{v_schema_name}}.{{v_src_table.table_name}}', 'xxx_{{v_src_table.table_name}}_{{v_ts}}'
  exec sp_rename '{{v_schema_name}}.{{v_src_table.table_name}}_pk', 'xxx_{{v_src_table.table_name}}_pk_{{v_ts}}'
end
;

create table {{v_schema_name}}.{{v_src_table.table_name}} (
    {{v_src_table.table_name}}_sid integer NOT NULL IDENTITY(1,1),
    {%- for feld in v_src_table.columns %}
    {%- if feld["pk"] == 1 %} {%- set ns.has_pk = 1 -%} {%- endif %}
    {{ "," if not loop.first else " " }}{{feld["column_name"]}} {{feld["data_type"]}} {{feld["mandatory"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk nvarchar(10) {{feld["mandatory"]}}
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk nvarchar(8) {{feld["mandatory"]}}
    {%- endif %}
    {%- endfor -%}
    -- Standard fields   
    ,dwh_ValidFrom datetime NOT NULL
    ,dwh_ValidTo datetime NOT NULL
    ,dwh_CurrentFlag integer NOT NULL
    ,dwh_DeleteFlag integer NOT NULL
    ,dwh_EarlyArriveFlag integer NOT NULL
    ,dwh_EarlyArriveField nvarchar(255) NOT NULL
    ,dwh_InsertDate datetime NOT NULL
    ,dwh_UpdateDate datetime NULL
    ,dwh_BatchRunIdInsert integer NOT NULL
    ,dwh_BatchRunIdUpdate integer NULL
    {# mandatory constraint SID  #}
    ,constraint {{v_src_table.table_name}}_pk primary key ({{v_src_table.table_name}}_sid)
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
    {{v_src_table.table_name}}_sid

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
    -- Standard fields    
    ,dwh_ValidFrom
    ,dwh_ValidTo
    ,dwh_CurrentFlag
    ,dwh_DeleteFlag
    ,dwh_EarlyArriveFlag
    ,dwh_EarlyArriveField
    ,dwh_InsertDate
    ,dwh_UpdateDate
    ,dwh_BatchRunIdInsert
    ,dwh_BatchRunIdUpdate    
from dwh.{{v_src_table.table_name}}
where 1=1
    and dwh_CurrentFlag = 1
    and dwh_DeleteFlag = 0
    and dwh_EarlyArriveFlag = 0
;

if exists (select 1 
from  sysobjects where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_cid')
 and type = 'V')
 drop view {{v_schema_name}}.v_{{v_src_table.table_name}}_cid
;

create view {{v_schema_name}}.v_{{v_src_table.table_name}}_cid as
select
    {{v_src_table.table_name}}_sid

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
    -- Standard fields    
    ,dwh_ValidFrom
    ,dwh_ValidTo
    ,dwh_CurrentFlag
    ,dwh_DeleteFlag
    ,dwh_EarlyArriveFlag
    ,dwh_EarlyArriveField
    ,dwh_InsertDate
    ,dwh_UpdateDate
    ,dwh_BatchRunIdInsert
    ,dwh_BatchRunIdUpdate    
from {{v_src_schema_name}}.{{v_src_table.table_name}}
where 1=1
    and dwh_CurrentFlag = 1
; 

if exists (select 1 
from  sysobjects where id = object_id('{{v_schema_name}}.v_{{v_src_table.table_name}}_fhi')
 and type = 'V')
 drop view {{v_schema_name}}.v_{{v_src_table.table_name}}_fhi
;

create view {{v_schema_name}}.v_{{v_src_table.table_name}}_fhi as
select
    {{v_src_table.table_name}}_sid

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
    -- Standard fields    
    ,dwh_ValidFrom
    ,dwh_ValidTo
    ,dwh_CurrentFlag
    ,dwh_DeleteFlag
    ,dwh_EarlyArriveFlag
    ,dwh_EarlyArriveField
    ,dwh_InsertDate
    ,dwh_UpdateDate
    ,dwh_BatchRunIdInsert
    ,dwh_BatchRunIdUpdate    
from {{v_src_schema_name}}.{{v_src_table.table_name}}
where 1=1
;     
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
    {%- for feld in v_src_table.columns %}
    {{ "," if not loop.first else " " }}{{feld["column_name"]}} = {{feld["default"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk = '-1'
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk = '-1'
    {%- endif %}    
    {%- endfor %}
    -- Standard fields    
    ,dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 0        
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
    {%- for feld in v_src_table.columns %}
    {{ "," if not loop.first else " " }}{{feld["column_name"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk = convert(nvarchar(10), {{feld["column_name"]}}, 120)
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk = convert(nvarchar(8), {{feld["column_name"]}}, 14)
    {%- endif %}    
    {%- endfor %}
    --Standard fields   
    ,dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 0    
  from {{v_schema_name}}.v_{{v_src_table.table_name}}_91
end
;
"""

tmpl_proc_sta_delete_detection_SQL = """
{# bk suchen, das letzte Feld mit bk Flag wird genommen! #}
{%- set ns = namespace(bk_name='') -%}
{%- for feld in v_src_table.columns -%}
{%- if feld["bk"] == 1 %} {%- set ns.bk_name = feld["column_name"] -%} {%- endif %}
{%- endfor -%}

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
    {%- for feld in v_src_table.columns %}
    {{ "," if not loop.first else " " }}{{feld["column_name"]}}
    {%- set data_type = feld["data_type"]  -%}
    {%- if data_type == 'datetime' or data_type == 'date' %}
    ,dim_Date_{{feld["column_name"]}}_bk
    {%- endif %}
    {%- if data_type == 'datetime' %}
    ,dim_Time_{{feld["column_name"]}}_bk
    {%- endif %}    
    {%- endfor %}
    -- Standard fields
    ,dwh_BatchRunIdInsert = @BatchRunIdInsert
    ,dwh_DeleteFlag = 1       
  from {{v_src_schema_name}}.{{v_src_table.table_name}} dwh
    where 1=1 
	and {{v_src_schema_name}}.dwh_CurrentFlag = 1    
    and {{v_src_schema_name}}.dwh_DeleteFlag = 0
    and {{v_src_schema_name}}.dwh_EarlyArriveFlag = 0
    and not exists (
        select *
        from {{v_schema_name}}.{{v_src_table.table_name}} stg
        where {{v_schema_name}}.{{ns.bk_name}} = {{v_src_schema_name}}.{{ns.bk_name}}
    )
end
;
"""


tmpl_proc_sta_historization_SQL = """
{# bk suchen, das letzte Feld mit bk Flag wird genommen! #}
{%- set ns = namespace(bk_name='') -%}
{%- for feld in v_src_table.columns -%}
{%- if feld["bk"] == 1 %} {%- set ns.bk_name = feld["column_name"] -%} {%- endif %}
{%- endfor -%}

if exists (select 1 
from sysobjects where id = object_id('{{v_src_schema_name}}.usp_{{v_src_table.table_name}}_historization')
  and type = 'P')
  drop procedure {{v_src_schema_name}}.usp_{{v_src_table.table_name}}_historization
;

CREATE PROCEDURE {{v_src_schema_name}}.usp_{{v_src_table.table_name}}_historization
    @dwh_BatchRunIdInsert     int
    ,@dwh_Init_ValidFrom      datetime
    ,@dwh_ValidFrom           datetime    
    ,@dwh_ValidTo             datetime    
AS
BEGIN       
    
    IF @dwh_ValidFrom IS NULL
    BEGIN
        SELECT @dwh_ValidFrom = convert(datetime2(0),getdate())
    END
    
    SELECT @dwh_ValidTo = dateadd(ss,-1,@dwh_ValidFrom)

    -- Upsert case
    INSERT INTO {{v_schema_name}}.{{v_src_table.table_name}}  
        (
        {%- for feld in v_src_table.columns %}
        {{ "," if not loop.first else " " }}{{feld["column_name"]}}
        {%- set data_type = feld["data_type"]  -%}
        {%- if data_type == 'datetime' or data_type == 'date' %}
        ,dim_Date_{{feld["column_name"]}}_bk
        {%- endif %}
        {%- if data_type == 'datetime' %}
        ,dim_Time_{{feld["column_name"]}}_bk
        {%- endif %}    
        {%- endfor %}
        ,dwh_ValidFrom
        ,dwh_ValidTo
        ,dwh_CurrentFlag
        ,dwh_DeleteFlag     
        ,dwh_EarlyArriveFlag    
        ,dwh_EarlyArriveField
        ,dwh_InsertDate
        ,dwh_UpdateDate
        ,dwh_BatchRunIdInsert
        ,dwh_BatchRunIdUpdate
        )
    SELECT
        {%- for feld in v_src_table.columns %}
        {{ "," if not loop.first else " " }}{{feld["column_name"]}}
        {%- set data_type = feld["data_type"]  -%}
        {%- if data_type == 'datetime' or data_type == 'date' %}
        ,dim_Date_{{feld["column_name"]}}_bk
        {%- endif %}
        {%- if data_type == 'datetime' %}
        ,dim_Time_{{feld["column_name"]}}_bk
        {%- endif %}    
        {%- endfor %}
        --,dwh_ValidFrom            = getdate()
        ,dwh_ValidFrom              = @dwh_ValidFrom
        ,dwh_ValidTo                = '9999-12-31 23:59:59'
        ,dwh_CurrentFlag            = 1
        ,dwh_DeleteFlag     
        ,dwh_EarlyArriveFlag        
        ,dwh_EarlyArriveField       
        ,dwh_InsertDate             = getdate()
        ,dwh_UpdateDate             = null
        --,dwh_BatchRunIdInsert     = -1
        ,dwh_BatchRunIdInsert       = @dwh_BatchRunIdInsert
        ,dwh_BatchRunIdUpdate       = null     
    FROM (
         MERGE {{v_schema_name}}.{{v_src_table.table_name}}  as dwh

    USING (
        SELECT                     
            {%- for feld in v_src_table.columns %}
            {{ "," if not loop.first else " " }}{{feld["column_name"]}}
            {%- set data_type = feld["data_type"]  -%}
            {%- if data_type == 'datetime' or data_type == 'date' %}
            ,dim_Date_{{feld["column_name"]}}_bk
            {%- endif %}
            {%- if data_type == 'datetime' %}
            ,dim_Time_{{feld["column_name"]}}_bk
            {%- endif %}    
            {%- endfor %}
            ,dwh_DeleteFlag
            ,dwh_EarlyArriveFlag        = 0 
            ,dwh_EarlyArriveField       = '#NA#'
        FROM {{v_src_schema_name}}.{{v_src_table.table_name}} stg 
        ) as stg
        ON {{v_schema_name}}.{{ns.bk_name}} = {{v_src_schema_name}}.{{ns.bk_name}}
          AND {{v_schema_name}}.dwh_CurrentFlag = 1
        WHEN MATCHED AND
            (
            {%- for feld in v_src_table.columns %}
            {{ "OR" if not loop.first else "" }} {{v_schema_name}}.{{feld["column_name"]}} <> {{v_src_schema_name}}.{{feld["column_name"]}}
            {%- set data_type = feld["data_type"]  -%}
            {%- if data_type == 'datetime' or data_type == 'date' %}
            OR {{v_schema_name}}.dim_Date_{{feld["column_name"]}}_bk <> {{v_src_schema_name}}.dim_Date_{{feld["column_name"]}}_bk
            {%- endif %}
            {%- if data_type == 'datetime' %}
            OR {{v_schema_name}}.dim_Time_{{feld["column_name"]}}_bk <> {{v_src_schema_name}}.dim_Time_{{feld["column_name"]}}_bk
            {%- endif %}    
            {%- endfor %}           
            OR  {{v_schema_name}}.dwh_DeleteFlag       <> {{v_src_schema_name}}.dwh_DeleteFlag     
            OR  {{v_schema_name}}.dwh_EarlyArriveFlag  <> {{v_src_schema_name}}.dwh_EarlyArriveFlag
            OR  {{v_schema_name}}.dwh_EarlyArriveField <> {{v_src_schema_name}}.dwh_EarlyArriveField
            )
        THEN UPDATE SET
             {{v_schema_name}}.dwh_CurrentFlag          = 0
            ,{{v_schema_name}}.dwh_ValidTo              = @dwh_ValidTo
            ,{{v_schema_name}}.dwh_UpdateDate           = getdate()
            ,{{v_schema_name}}.dwh_BatchRunIdUpdate     = @dwh_BatchRunIdInsert
        OUTPUT 
            $action as Act
            ,{{v_src_schema_name}}.*
    ) MergeOutput 
    WHERE MergeOutput.Act = 'UPDATE'

--- hier war mal ein Strichpunkt

    -- new records: Insert
    INSERT INTO {{v_schema_name}}.{{v_src_table.table_name}}
    SELECT 
        {%- for feld in v_src_table.columns %}
        {{ "," if not loop.first else " " }}{{feld["column_name"]}}
        {%- set data_type = feld["data_type"]  -%}
        {%- if data_type == 'datetime' or data_type == 'date' %}
        ,dim_Date_{{feld["column_name"]}}_bk
        {%- endif %}
        {%- if data_type == 'datetime' %}
        ,dim_Time_{{feld["column_name"]}}_bk
        {%- endif %}    
        {%- endfor %}
        --,dwh_ValidFrom                = '2023-08-06 14:00:00'
        ,dwh_ValidFrom              = @dwh_Init_ValidFrom
        ,dwh_ValidTo                = '9999-12-31 23:59:59'
        ,dwh_CurrentFlag            = 1
        ,dwh_DeleteFlag     
        ,dwh_EarlyArriveFlag        = 0 
        ,dwh_EarlyArriveField       = '#NA#'
        ,dwh_InsertDate             = getdate()
        ,dwh_UpdateDate             = null
        ,dwh_BatchRunIdInsert       = @dwh_BatchRunIdInsert
        --,dwh_BatchRunIdInsert     = -1
        ,dwh_BatchRunIdUpdate       = null
    FROM {{v_src_schema_name}}.{{v_src_table.table_name}} stg
    WHERE NOT EXISTS (          
        SELECT *
        FROM {{v_schema_name}}.{{v_src_table.table_name}} dwh
        WHERE {{v_schema_name}}.{{ns.bk_name}} = {{v_src_schema_name}}.{{ns.bk_name}}
        AND {{v_schema_name}}.dwh_CurrentFlag    = 1
        )
        
END

"""

# Pipeline Felder: Name, Ziel_Schema, Quell_Schema, Template Name

job_pipeline_old = (
('sta_90er_view',             sta_schema_name, sta_schema_name, tmpl_sta_90er_view_SQL),
('sta_91er_view',             sta_schema_name, sta_schema_name, tmpl_sta_91er_view_SQL),
('sta_table',                 sta_schema_name, sta_schema_name, tmpl_sta_table_SQL),
('dwh_table',                 dwh_schema_name, dwh_schema_name, tmpl_dwh_table_SQL),
('rep_views',                 rep_schema_name, dwh_schema_name, tmpl_rep_views_SQL),
('proc_sta_dummy',            sta_schema_name, sta_schema_name, tmpl_proc_sta_dummy_SQL),
('proc_sta_full_load',        sta_schema_name, sta_schema_name, tmpl_proc_sta_full_load_SQL),
('proc_sta_delete_detection', sta_schema_name, dwh_schema_name, tmpl_proc_sta_delete_detection_SQL),
('proc_sta_historization',    dwh_schema_name, sta_schema_name, tmpl_proc_sta_historization_SQL)
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
#                       Man könnte den Generator so gestalten, dass er immer ein rename Table erzeugt und die neuen NOT NULL Felder immer mit den dummy Werten initialiseirt.
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
    # init DB Connection
    server = "itxchdm.switzerlandnorth.cloudapp.azure.com"
    database = "NGDWA"
    username = "chdm"
    password = "IT-Logix32"

    ret = 0

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

    return ret


def get_dummy_value_per_datatype(datatype, column_name, mandatory):
    if mandatory == "NULL":
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
    else:      # Datentyp "N/A"!!
       dummy_value = "" 
    return dummy_value



def setStandardDefaults(p_tabledef):
    #in der Tabellendefinition Standarddefaults einsetzen. Falls "default" <> "" wird nichts gemacht!
    v_tabledef = p_tabledef
    i = 0
    for feld in v_tabledef["columns"]:  
        if feld["default"] == "":
            #print(feld["data_type"], feld["column_name"], feld["mandatory"])
            v_default = get_dummy_value_per_datatype(feld["data_type"], feld["column_name"], feld["mandatory"])
            v_tabledef["columns"][i]["default"] = v_default
        i += 1    
    return v_tabledef



def build_query(template, p_tg_schema_name, p_src_schema_name, p_src_table, p_ts):    
    script = ''    
    try:
        environment = jinja2.Environment()
        template = environment.from_string(template)
        script = template.render(v_schema_name=p_tg_schema_name, v_src_table=p_src_table, v_ts=p_ts, v_src_schema_name=p_src_schema_name)
    except jinja2.TemplateError as error:
        logger.error("In build_query gibt es einen Jinja Fehler: " + str(error))
    except:
        logger.error("In build_query gibt es einen unbekannten Fehler.")
    return(script)
    
    
def get_source_files(p_path):
    ret = []
    for (dirpath, dirs, files) in os.walk(p_path):
        #print(dirpath)
        for filename in files:
            if os.path.exists(dirpath + "/" + filename):
                ret.append(filename)
    return ret


def read_source_def(p_filename):
    ret = {}
    try:
        f = open(p_filename)
        ret = yaml.safe_load(f)
        f.close()
    except:
        logger.error("Fehler in read_source_def. Parameter: " + p_filename) 
    
    return ret


def read_template(p_filename):
    ret = """ """
    try:
        f = open(p_filename)
        ret = f.read()
        f.close()
    except:
        logger.error("Fehler in read_template. Parameter: " + p_filename) 
    
    return ret



def run_jobs(p_name, p_jobs, p_table, p_ts):
    ret = 0
    try:
        einzelJobAuswahl = '*'    #'sta_91er_view'     #'proc_sta_historization'  

        for job in p_jobs:
            if ret == 0:
                if (einzelJobAuswahl == (job[0])) or (einzelJobAuswahl == ('*')):
                    print('\n****************************************\n', 
                          job[0], 
                          '\n****************************************\n')
                    logger.info("Run: " + job[0] + " / " + p_name)
                    
                    #sql = build_query(job[3], job[1], job[2], p_table, p_ts)
                    #ret = execute_statements(sql)
                    
                    if ret != 0:
                        logger.error("execute_statements: " + ret)        
        
    except:
        logger.error("In run_jobs gibt es einen unbekannten Fehler.")    
    
    return ret
    
####################### MAIN EXECUTION ###############################

start_time = time.time()      # Zeitmessung

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

    
# einen Timestamp für die Pipeline generieren
jetzt = dt.now()
jetztString = jetzt.strftime("%Y%m%d%H%M%S")
if printInfo:
    print (jetztString)

# Liste Sourcefiles erstellen   TEMP!!!
list_tables = get_source_files(source_dir)
print('list_tables ')
print(list_tables)

vRet, vSubdirs = getSubdirs(template_dir)
if vRet==0:
    print(vSubdirs)
    if len(vSubdirs)>0:
        for sd in vSubdirs:
            if sd == run_templates:
                vRet2, vFiles = getFiles(template_dir + sd + '/')
                if vRet2==0:
                    print(vFiles)
                    if tasks_name in vFiles:
                        #YAML File auseinandernehmen
                        with open(template_dir + run_templates + '/' + tasks_name, 'r') as f:
                            data = yaml.safe_load(f)
                            #print(data['schemas'])
                            
                            vSchema = next(item for item in data['schemas'] if item["name"] == 'sta_schema_name')
                            sta_schema_name = vSchema['db_schema']
                            vSchema = next(item for item in data['schemas'] if item["name"] == 'dwh_schema_name')
                            dwh_schema_name = vSchema['db_schema']
                            vSchema = next(item for item in data['schemas'] if item["name"] == 'rep_schema_name')
                            rep_schema_name = vSchema['db_schema']
                            
                            job_pipeline = data['tasks']
                            
                            for job in job_pipeline:
                                print(job['name'])
                                print("   " + job['quell_schema'])
                                print("   " + job['ziel_schema'])
                                print("   " + job['tmpl_name'])
                                
                    else:
                        logger.error("Kein tasks.yml File in "  + run_templates + " gefunden!" )
                        exit(1)
            else:
                logger.warning("Template Gruppe " + run_templates + " nicht gefunden!")


# Queries generieren (und ausführen)
#----- !!!!!!!! ---------

table_select = '*'     #'dim_Study.yml'
for run in list_tables:
    if (table_select == '*') or (table_select == run):
        src_table = {}
        src_table = read_source_def(source_dir + run)
        #print("--------------------------------------------------")
        print(" RUN: ", run)
        #print("--------------------------------------------------")
        # Defaults in der Tabelle ergänzen
        src_table = setStandardDefaults(src_table)
        result = run_jobs(run, job_pipeline, src_table, jetztString)
        #print("--------------------------------------------------")
        print(" END: ", run)
        #print("--------------------------------------------------")

                
end_time = time.time()
dauer = end_time - start_time
print("Laufzeit: " + str(datetime.timedelta(seconds = dauer)))

