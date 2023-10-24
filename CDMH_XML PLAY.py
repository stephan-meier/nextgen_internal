import xmltodict
import json

xmlInFile = "C:/Users/steph/Downloads/PDM_CHDM.pdm"
jsonOutFile = "C:/Users/steph/Downloads/PDM_CHDM.json"

with open(xmlInFile, encoding='utf-8') as fd:
    doc = xmltodict.parse(fd.read(),process_namespaces=True)

file = open(jsonOutFile,"w")
json.dump(doc,file)
file.close()

m_t = doc["Model"]["object:RootObject"]["collection:Children"]["object:Model"]["collection:Tables"]
for t in m_t["object:Table"]:
    print(t["attribute:Name"])
    for c in t["collection:Columns"]["object:Column"]:
        print("       ", c["attribute:Name"], " / ", c["attribute:DataType"], " / ", c["attribute:Comment"])


