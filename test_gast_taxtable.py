import httplib, urllib, urllib2
import json
from dbconn import test_engine
from threading import Thread
import time


def createObject(data_json, object_str):
    headers = {'content-type': 'application/json'}
    conn = httplib.HTTPConnection("localhost:8080")
    conn.request("POST", "/mobedac_ws/" + object_str, data_json, headers)
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    print data
    conn.close()
    return data

def getObject(object_type, obj_id):
    conn = httplib.HTTPConnection("localhost:8080")
    conn.request("GET", "/mobedac_ws/" + object_type + "/" + str(obj_id))
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data
    
def getListenerResults():
    conn = httplib.HTTPConnection("localhost:8081")
    conn.request("GET", "/get_requests")
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data
def clearListenerResults():
    conn = httplib.HTTPConnection("localhost:8081")
    conn.request("GET", "/clear_requests")
    response = conn.getresponse()
    conn.close()

submission_data_l1_only = {"library_ids" : ['l1'
                                    #, 
                                    #'l2',
                                    # 'l3', 'l0', 'ls0'
                                     ],
        "analysis_params": {
            "user":"mobedac",
            "auth" : "asdfasdfasdf"}
   }
submission_data_l123 = {"library_ids" : ['l1','l2','l3'],
        "analysis_params": {
            "user":"mobedac",
            "auth" : "asdfasdfasdf"}
   }
def postSubmission(submission_object):
    return createObject(json.dumps(submission_object), "submission")

def change_sequence_file_type(new_type):
    urllib2.urlopen("http://localhost:8081/mobedac/set_sequence_set_file_type/" + new_type)                

# main routine for each submission request we want to make
# first clears the db
# then tells the mobedac_vamps_listener process to clear out any data it has accumulated
def test_by_type(seq_file_type, submission_object, expected_names):
    print "***** Starting test for file type: " + seq_file_type
    
    test_engine.execute("Delete from submission_details;")
    test_engine.execute("Delete from submission;")
    
    # clear all requests from listener
    clearListenerResults()
    
    # now create a request
    change_sequence_file_type(seq_file_type)
    submission_id = postSubmission(submission_object)
    
    # now we need to loop and check status
    while True:
        # get the status of the submission
        submission_str = getObject("submission", submission_id)
        submission_json = json.loads(submission_str)
        overall_status = submission_json['status_code']
        if overall_status == 1:
            # call over to the mobedac_vamps_listener.py process and get 
            # the list of all calls that it registered made to it from our API service
            listener_calls = getListenerResults()
            print "Calls made to Mobedac: " + listener_calls
            print "Expcted Calls Mobedac: " + str(expected_names)
            # are they ok?
            listener_calls_array = json.loads(listener_calls)
            if len(listener_calls_array) != len(expected_names ):
                print "Incorrect number of calls to VAMPS and Mobedac got: " + str(len(listener_calls_array)) 
            error = False
            for actual,expected in zip(listener_calls_array,expected_names):
                if actual != expected:
                    error = True
                    print "Incorrect call, expected: " + expected + " got: " + actual
                    break
            if error == False:
                print "Success!!! for " + seq_file_type
                break
            else:
                print "Fail for " + seq_file_type
                break
        time.sleep(10)

# should post 3 times, gast twice, and tax table once and 1 data return
expected_names_123 = ['upload_data_post', 'upload_data_post', 'upload_data_post', 'upload_data_gast', 'generate_taxonomy_table', 'POST results']
#expected_names = ['upload_data_post', 'upload_data_gast', 'generate_taxonomy_table', 'POST results']
test_by_type('fasta', submission_data_l123, expected_names_123)
#test_by_type('fasta', submission_data_l1_only, expected_names)
#test_by_type('fastq_small', submission_data_l1_only, expected_names)
#test_by_type('sff_small',submission_data_l1_only, expected_names)
#test_by_type('fastq_large', expected_names)

