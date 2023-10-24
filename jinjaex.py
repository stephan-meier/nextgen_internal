import jinja2
import json


j1 = """
{
    "product": "Apple Juice",
    "life_span": 180,
    "made_in" : "Singapore"
}
"""

t1 = """
{% if life_span > 160 and life_span < 180 %}
    {{product}} is expiring soon!
{% elif life_span >= 180 %}
    {{product}} has expired!
{% else %}
    It's perfect
{% endif %}
"""

j2 = """
{
    "fruit": [
        {
            "key": 1,
            "value": "Apple"
        },
        {
            "key": 2,
            "value": "Banana"
        },
        {
            "key": 3,
            "value": "Orange"
        }
    ]
}
"""

t2 = """
-------------------------------
{%- for fruit in fruit -%}
    {%- for key, value in fruit.items() %}
        {{key}} : {{value|lower}}
    {%- endfor %}
{%- endfor %}
--------------------------
"""

j3 = """
{
    "tabelle": {
        "name": "tabelle1",
        "loadtyp": "full",
        "dbtyp": "SQLServer",
        "felder": [
            {
                "feld": "ID",
                "ftyp": "integer",
                "nullable": 0,
                "PK": 1,
                "BK": 1,
                "default": -1,
                "description": "Primary Key"
            },
            {
                "feld": "Name",
                "ftyp": "nvarchar(50)",
                "nullable": 1,
                "PK": 0,
                "BK": 0,
                "default": "N/A",
                "description": "xx"
            },
            {
                "feld": "Ort",
                "ftyp": "nvarchar(50)",
                "nullable": 1,
                "PK": 0,
                "BK": 0,
                "default": "N/A",
                "description": ""
            },
            {
                "feld": "Kategorie",
                "ftyp": "integer",
                "nullable": 1,
                "PK": 0,
                "BK": 0,
                "default": "-1",
                "description": "xx"
            }
        ]
    }
}
"""


environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")
r = template.render(name="World")
print(r)

pj = json.loads(j1)
template = environment.from_string(t1)
r = template.render(product=pj["product"], life_span=pj["life_span"])
print(r)

pj = json.loads(j2)
template = environment.from_string(t2)
r = template.render(fruit=pj["fruit"]) 
print(r)

pj = json.loads(j3)
print(pj["tabelle"]["name"])
for f in pj["tabelle"]["felder"]:
    print(f["feld"], ": ", f["ftyp"])
    
    
    

from jinja2 import Template 
def clever_function():
 return "Hello"
	
template = Template("{{ clever_function() }}") 
print(template.render(clever_function=clever_function))





from jinja2 import Template

def custom_function(a):
    return a.replace('o', 'ay')

template = Template('Hey, my name is {{ custom_function(first_name) }} {{ func2(last_name) }}')
template.globals['custom_function'] = custom_function

fields = {'first_name': 'Jo', 'last_name': 'Ko', 'func2': custom_function}
print (template.render(**fields))

