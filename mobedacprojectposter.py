import httplib, urllib
import json

data = {'name': 'MBLTestProject', 'about': 'This is projectG update2', 'url' : 'testurl', 'pi' : 'John Hufnagle', 'samples' : [],
        "funding_source" : "keck",
        "description" : "project S description",
"metadata":
    {
}
   }
data_json = json.dumps(data)
headers = {'content-type': 'application/json'}
conn = httplib.HTTPConnection("mobedac.org")
conn.request("PUT", "/api.cgi/project", data_json, headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()
print data
conn.close()