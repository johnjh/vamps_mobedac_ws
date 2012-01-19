import httplib, urllib
import json

data = {'name': 'Submission', 'about': 'This is sample', 'url' : 'testurl', "project" : "3", "sample" : "mgs653", "library" : "2", "options" : "no options", "sequence_set" : "4",
        "type" : "amplicon",
        "metadata": {
            "sample1":"European"},
        "options" : {
            "domain" : "Archaeal",
            "action" : "process",
            "user"   : "mobedac",
            "project_name_code" : "JJH_TSTP"
                     }
   }
   
data_json = json.dumps(data)
headers = {'content-type': 'application/json'}
conn = httplib.HTTPConnection("localhost:8080")
conn.request("POST", "/submission", data_json, headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()
print data
conn.close()