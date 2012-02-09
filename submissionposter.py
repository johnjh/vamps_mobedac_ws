import httplib, urllib
import json

data = {"library_ids" : ['l1', 'l2', 'l3', 'l0', 'ls0'],
        "analysis_params" : {
            "user"   : "mobedac",
                     }
   }
   
data_json = json.dumps(data)
headers = {'content-type': 'application/json'}
conn = httplib.HTTPConnection("localhost:8080")
conn.request("POST", "/mobedac_ws/submission", data_json, headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()
print data
conn.close()