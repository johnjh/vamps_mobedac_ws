#!/usr/bin/python
import cherrypy
import threading
import time
from submissionorm import SubmissionORM
from projectorm import ProjectORM
from libraryorm import LibraryORM
from sampleorm import SampleORM
#import json as jsonmgl190
import json as json
from Bio import SeqIO
import os
from string import Template
from rest_log import mobedac_logger
from poster import streaminghttp 
from poster import encode
import urllib2, urllib
from urllib2 import URLError, HTTPError
from sqlalchemy import *
from sqlalchemy import  and_
from dbconn import Session, test_engine
from initparms import get_parm
from submission_detailsorm import SubmissionDetailsORM
from shutil import rmtree
from metadata_maps import samplemetadatamap, sequencemetadatamap

class Submission_Processor (threading.Thread):
    MOBEDAC_SEQUENCE_FILE_NAME = "mobedac_sequences.seq"
    MOBEDAC_SEQUENCE_FILE_NAME_PREFIX = "mobedac_sequences"
    MOBEDAC_RESULTS_FILE_NAME = "vamps_results.json"
    
    # some VAMPS processing code
    VAMPS_TRIM_SUCCESS = "TRIM_SUCCESS"
    VAMPS_GAST_COMPLETE = "GAST_SUCCESS"

    def __init__(self, sleep_seconds, vamps_upload_url, vamps_gast_url, processing_dir):
        self.sleep_seconds = sleep_seconds
        self.exitFlag = False
        self.vamps_upload_url = vamps_upload_url
        self.vamps_gast_url = vamps_gast_url
        self.root_dir = processing_dir
        self.halt_processing = False
        # these are the 2 important dictionary maps that map an incoming MOBEDAC metadata field/value into the correct table/column in our db
        self.sample_related_metadata_map_json = samplemetadatamap
        self.sequence_related_metadata_map_json = sequencemetadatamap
        
        threading.Thread.__init__(self)
     
    # populates a hash (dictionary) and the values are lists
    # this routine takes care of the bookeeping of seeing if the key
    # is already present in the dictionary.  If it is not present
    # then we add an empty list to the dictionary with that key
    # and then add the object value to that list
    #
    # if the key was already present in the dictionary then we simply
    # add the obj to that value list 
    #
    # as an example...
    # so this can be used to organize parent's and their children.
    # it is used often in this code to organize Submission and SubmissionDetail
    # objects that have been read from the db
    # if each child object has a parent id you could loop through each
    # and call this method as:
    #
    #  children_by_parent_dictionary = {}
    #  for child_obj in array_of_child_objects_of_various_parents:
    #     self.accumulate_by_key(children_by_parent_dictionary, child_obj.parent_id, child_obj)
    #
    # and when it completed you would have a dictionary of:
    # 
    # {
    #    'parent A id' : [ child_1_of_parent_A, child_2_of_parent_A, ...],
    #    'parent B id' : [ child_1_of_parent_B, child_2_of_parent_B, ...],
    #    ...
    # }
    #
    def accumulate_by_key(self, hash, key, obj):
        temp_array = hash.get(key, None)
        if temp_array == None:
            hash[key] = temp_array = []
        temp_array.append(obj)        
        
    def log_debug(self, msg):
        mobedac_logger.debug(msg)
        
    def log_info(self, msg):
        mobedac_logger.info(msg)

    def log_exception(self, msg):
        mobedac_logger.exception(msg)
        
    def stop_processing(self):   
        self.exitFlag = True
        
    def disable_processing(self):   
        self.log_debug("Disabling processor")
        self.halt_processing = True
        
    def enable_processing(self):   
        self.log_debug("Enabling processor")
        self.halt_processing = False

    def log_to_submission_detail(self, submission_detail, msg):
        self.log_exception(msg)
        submission_detail.current_status_msg = msg
        self.sess_obj.commit()

    def log_to_submission(self, submission, msg):
        self.log_exception(msg)
        submission.current_status_msg = msg
        self.sess_obj.commit()

    def clear_submission_msg_text(self, submissiondetail_array):
        for detail in submissiondetail_array:
            detail.current_status_msg = None
        self.sess_obj.commit()
        
    def set_submission_details_next_action(self, submissiondetail_array, next_action):
        for detail in submissiondetail_array:
            detail.next_action = next_action
        self.sess_obj.commit()
        
    def get_submission_processing_dir(self, submission):
        return os.path.join(self.root_dir,str(submission.id))

    def get_submission_detail_processing_dir(self, submission, submissiondetail):
        return os.path.join(self.get_submission_processing_dir(submission), str(submissiondetail.id))

    def create_submission_processing_dir(self, submission):
        processing_dir = self.get_submission_processing_dir(submission)
        if os.path.exists(processing_dir) == False:
            os.mkdir(processing_dir)
        return processing_dir

    def create_submission_detail_processing_dir(self, submission, submissiondetail):
        self.create_submission_processing_dir(submission) 
        processing_dir = self.get_submission_detail_processing_dir(submission, submissiondetail)
        if os.path.exists(processing_dir) == False:
            os.mkdir(processing_dir)
        return processing_dir
    
    def run(self):
        # Register the streaming http handlers with urllib2
        streaminghttp.register_openers()
        # start the work
        while True:
            # sleep 30 seconds...this should be parameterized
            time.sleep(30)
            if self.halt_processing == False:
                self.log_debug("processing wakeup...")
                if self.exitFlag:
                    return;
                # find all submission_details objects that are want to have their data downloaded from MOBEDAC and processed
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_DOWNLOAD)
                if self.exitFlag:
                    return;
                # find all submission_details objects that are want to uploaded to VAMPS for processing
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_VAMPS_UPLOAD)
                if self.exitFlag:
                    return;
                # find all submission_details objects that are want to be GASTed by VAMPS
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_GAST)
                if self.exitFlag:
                    return;
                # now return the answers to MOBEDAC
                self.return_results_to_mobedac()
                if self.exitFlag:
                    return;

    # perform the action on the submissions in the db
    # this routine does a search for the given action string
    # 
    def perform_action_on_submissions(self, action):
        self.sess_obj = None
        try:
            self.sess_obj = Session()
            details_hashed_by_submission_id = {}
                
            # get all pending submission detail objects and put them in a hash where each key is the submission id
            # and each value is an array of detail objects and the detail's next_action is the 'action' input parm
            details_hashed_by_submission_id = {}
            for detail in self.sess_obj.query(SubmissionDetailsORM).filter(SubmissionDetailsORM.next_action == action).all():
                self.accumulate_by_key(details_hashed_by_submission_id, detail.submission_id, detail)
                
            # loop over the dictionary key is submission id and the value is an array of detail objects
            for submission_id, detail_array in details_hashed_by_submission_id.items():
                # get the submission object from the db
                submission = self.sess_obj.query(SubmissionORM).filter(SubmissionORM.id == submission_id).one()
                # make sure the base processing dir is there
                # we do all our work in a processing directory
                self.create_submission_processing_dir(submission)
                if self.exitFlag:
                    return;
                try:
                    # assume all is well with these submission detail object(s)
                    # this is a msg log
                    self.clear_submission_msg_text(detail_array)
                    # find the action as a method/function on this SubmissionProcessor class
                    action_method = getattr(self, action)
                    # do the action...and call it
                    action_method(submission, detail_array)
                except:
                    self.log_exception("Got exception action: " + action + " processing submission id: " + str(submission.id))
        except:
            self.log_exception("error performing action on submission")
        finally:
            self.sess_obj.close()
            self.sess_obj = None

    # see if there are any complete sets of submission details 
    # that we can process and perhaps generate the tax table and return that to MoBEDAC
    def return_results_to_mobedac(self):
        self.sess_obj = None
        try:
            self.sess_obj = Session()
            details_hashed_by_submission_id = {}
                
            # get all submission detail objects that have a status of 'post_results_to_mobedac'
            # and group them in arrays that are the value of a dictionary whose key is the submission_id
            for detail in self.sess_obj.query(SubmissionDetailsORM).filter(SubmissionDetailsORM.next_action == SubmissionDetailsORM.ACTION_POST_RESULTS_TO_MOBEDAC).all():
                self.accumulate_by_key(details_hashed_by_submission_id, detail.submission_id, detail)
                
            # now loop over all the arrays of detail objects
            completed_detail_hashs_by_submission_id = {}
            for key, value in  details_hashed_by_submission_id.items():
                # for this submission id are all of the detail submission objects in the correct state?
                # run a query that finds all submission detail objects that have this submission_id
                # and that don't have the SubmissionDetailsORM.ACTION_POST_RESULTS_TO_MOBEDAC value
                # as their next action.  if we find any then we know that this submission object has detail
                # objects that have not completed processing..so skip this submission object
                if len(self.sess_obj.query(SubmissionDetailsORM).filter(and_(SubmissionDetailsORM.submission_id == key, SubmissionDetailsORM.next_action != SubmissionDetailsORM.ACTION_POST_RESULTS_TO_MOBEDAC)).all()) > 0:
                    self.log_debug("There is a submission detail object associated with submission object: " + str(key) + " that does not have a next_action of: post_results_to_mobedac")
                    continue  # found a submission detail object attached to this submission object that does not have the expected 'action' status...so skip this submission object
                completed_detail_hashs_by_submission_id[key] = value
                
                # now do the work on each of these sets of details....send the data back to mobedac
                # loop through all the details in here and produce a list of datasets, and project counts
                sampleOrderNames = []
                library_ids = []
                unique_project_name_dict = {}
                details_by_library_id = {}
                some_detail_has_incomplete_gasting = False
                for detail in value:
                    # look into the VAMPS db and see if the status record for this detail object
                    # is completed yet?
                    status_row = detail.get_VAMPS_submission_status_row(self.sess_obj)
                    if status_row == None:
                        raise "Error locating vamps_upload_status record found for submission_detail: " + detail.id + " vamps_status_id: " + str(detail.vamps_status_record_id)
                    # could still be GAST'ing so we can't return info to mobedac yet
                    if status_row[0] != self.VAMPS_GAST_COMPLETE:
                        self.log_debug("Can't return results to MoBEDAC submissiondetail: " + str(detail.id) + " yet, VAMPS status row: " + str(detail.vamps_status_record_id) + " is still: " + status_row[0])
                        some_detail_has_incomplete_gasting = True
                        break
                    # keep track of unique project names by using a dictionary
                    unique_project_name_dict[detail.vamps_project_name] = detail.vamps_project_name
                    # keep a list of project-dataset names
                    sampleOrderNames.append(detail.vamps_project_name + "--" + detail.vamps_dataset_name)
                    # and library ids
                    library_ids.append(detail.library_id)
                    # remember these for sending back to mobedac
                    details_by_library_id[detail.library_id] = detail
                    
                if some_detail_has_incomplete_gasting:
                    continue # don't return results for this submission since there is still some processing going on
                
                # now we have all the sampleOrder names set up and a hash of the unique project names (we just want a count of those)
                project_count = len(unique_project_name_dict)
                # get the Submission object from the db
                submission = SubmissionORM.get_instance(key, self.sess_obj)
                taxonomy_table_json = self.get_taxonomy_table(project_count, sampleOrderNames, submission.user, 'family')
                if taxonomy_table_json == None:
                    self.log_debug("Didn't get any taxonomy returned from VAMPS for sampleOrderNames: " + str(sampleOrderNames))
                    continue
                # send the tax table to mobedac
                success = self.send_to_mobedac(submission, library_ids, details_by_library_id, taxonomy_table_json)
                # if all went well then mark all the details as complete
                if(success):
                    for detail in value:
                        detail.next_action = SubmissionDetailsORM.ACTION_PROCESSING_COMPLETE
                    self.sess_obj.commit()
                    # now we can delete the processing details directories but save the upper one
                    # because it has the results that were returned
                    processing_dir = self.get_submission_processing_dir(submission)
                    for detail in value:
                        rmtree(self.get_submission_detail_processing_dir(submission, detail))
                    
        except:
            self.log_exception("Got exception during taxonomy generation and mobedac sending")
        
    def get_analysis_links(self, user, details_by_library_id):
        links = {}
        for library, detail in details_by_library_id.items():
            links[library] = {"Visualization" : get_parm('vamps_landing_page_str') % (detail.vamps_project_name, user) }
        return links
    
    # POST the analysis results back to MoBEDAC
    # don't have the analysis links yet. 
    def send_to_mobedac(self, submission, library_ids, details_by_library_id, taxonomy_table_json):
        analysis_links = self.get_analysis_links(submission.user, details_by_library_id)
        mobedac_results_url = get_parm('mobedac_results_url')
        results_dict = {
                        "auth" : get_parm("mobedac_auth_key"),
                        "analysis_system" : "VAMPS",
                        "libraries"        : library_ids,
                        "analysis_links"   : analysis_links,
                        "taxonomy_table"   : json.loads(taxonomy_table_json)    
                        }       
        response = None 
        try:  
            # send it
            json_str = json.dumps(results_dict)
            # let's try to log this json into the processing dir
            # we are writing the json return data to a file in our processing dir just for safe keeping
            open(os.path.join(self.get_submission_processing_dir(submission),self.MOBEDAC_RESULTS_FILE_NAME), "w").write(json_str)
            req = urllib2.Request(mobedac_results_url, json_str, { 'Content-Type' : 'application/json' })
            response = urllib2.urlopen(req)
            self.log_info("POSTed results to MoBeDAC for submission: " +  str(submission.id) + " got response: " + response.read())
            return True        
        except HTTPError, e:
            self.log_exception('Error sending results to MoBEDAC, error code: ' + str(e.code))
            return False
        except URLError, e:
            self.log_exception('We failed to reach MoBEDAC server at: ' + mobedac_results_url + ' reason: ' + str(e.reason))           
            return False 
        finally:
            if response != None:
                response.close()
                       
    # call VAMPS to get tax table....if we fail then just return a None so we can deal with it better
    # this is a .php page that I created...I bet Andy could do a better job...should ask him.
    def get_taxonomy_table(self, project_count, projectDatasetNames, user, rank):
        taxonomy_table_url = get_parm('vamps_taxonomy_table_url')
        values = {'sampleOrder' : ",".join(projectDatasetNames),
                  'userProjects' : project_count,
                  'user' : user,
                  'taxonomicRank' : rank}                
        data = urllib.urlencode(values)
        response = None
        try:
            # generate the taxonomy table from VAMPS
            req = urllib2.Request(taxonomy_table_url, data)
            response = urllib2.urlopen(req)
            return response.read()        
        except HTTPError, e:
            self.log_exception('Error generating taxonomy table code: ' + str(e.code))
            return None
        except URLError, e:
            self.log_exception('We failed to reach the VAMPS server: ' + str(e.reason))             
            return None   
        finally:         
            if response != None:
                response.close()
            
    # Perform the processing to request a GAST from VAMPS
    # GASTing is performed on a whole project basis...VAMPS does not do dataset-by-dataset GASTing
    # all datasets in a project are GAST'ed together.
    # this means that we need to check that all vamps datasets in a particular project have successfully
    # had their TRIMing done to completion/success...otherwise we won't perform the GAST on their parent projects
    def gast(self, submission, submissiondetail_array):
        response = None
        try:
            # so we can have a collection of submissions to gast
            # if there are more than 1 details in a project then we want to gast them as a group
            # and so they all have to be at the state of TRIM_SUCCESS else we can't gast yet
            details_by_project_name = {}
            for detail in submissiondetail_array:                          
                status_row = detail.get_VAMPS_submission_status_row(self.sess_obj)
                if status_row == None:
                    raise "Error preparing for GAST no vamps_upload_status record found for submission_detail: " + str(detail.id) + " vamps_status_id: " + str(submission.vamps_status_record_id)
                if status_row[0] != self.VAMPS_TRIM_SUCCESS:
                    self.log_debug("Can't GAST submissiondetail: " + str(detail.id) + " yet, VAMPS status is: " + status_row[0])
                    return
                #gather them by project name
                self.accumulate_by_key(details_by_project_name, detail.vamps_project_name, detail)
            
            # write out the metadata
            self.writeMetadata(submission, submissiondetail_array)

            # if we land here then all submission detail objects in this project were uploaded and trimmed successfully and are waiting to be GASTed
            # need to GAST them by project
            # loop over all details by project
            for project_name, details in details_by_project_name.items():
                # can use just a single detail object because we GAST all the datasets in the project
                detail =  details[0]
                values = {'project' : project_name,
                          'new_source' : detail.region, 
                          'gast_ok' : '1',
                          'run_number' : str([d.vamps_status_record_id for d in details])  # this is a hack for testing purposes
                          }
                
                data = urllib.urlencode(values)
                # Create the Request object
                request = urllib2.Request(self.vamps_gast_url, data)
                # Actually do the request, and get the response
                # POST the GAST request to VAMPS
                response = urllib2.urlopen(request)
                if response.code != 200:
                    raise "Error starting GAST processing in VAMPS: " + response.msg
                # must have submitted ok so mark them all
                for detail in submissiondetail_array:                          
                    detail.next_action = SubmissionDetailsORM.ACTION_POST_RESULTS_TO_MOBEDAC
                self.sess_obj.commit()
            self.log_debug("Posted GAST for submissiondetail: " + str(detail.id) + " project: " + detail.vamps_project_name + " vamps status id: " + str(detail.vamps_status_record_id))
        except:
            self.log_exception("Some kind of error preparing to or actually calling VAMPS to GAST")
            self.log_to_submission(submission, "Some kind of error preparing to or actually calling VAMPS to GAST")
            raise
        finally:         
            if response != None:
                response.close()
                
    def rename_sample_name(self, metadata_dict):
        # rename the sample_id field to sample_id_str cuz we use an int in our db for this field
        sample_id_value = metadata_dict["SAMPLE_NAME"]
        del metadata_dict["SAMPLE_NAME"]
        metadata_dict["MOBEDAC_SAMPLE_ID"] = sample_id_value
        k = 5
         
    def uppercaseMetadataKeys(self, metadata_dict):
        uppercaseDict = {}
        for key,value in metadata_dict.items():
            uppercaseDict[key.upper()] = value
        return uppercaseDict
        
    # this routine loops over all the submission_detail objects for this submission
    # and gathers up a list of all of the sample ids, vamps project and dataset names
    # then loops over that set and inserts/updates metadata rows in each of the appropriate metadata normalized tables
    def writeMetadata(self, submission, submissiondetail_array):
        unique_sample_ids = {}
        for detail in submissiondetail_array:
            unique_sample_ids[detail.sample_id] = detail.sample_id
            
        # now loop over all samples, retrieve and store data
        for detail in submissiondetail_array:
            sample_obj = SampleORM.getFromMOBEDAC(detail.sample_id, None, self.sess_obj)
            sample_metadata_json = self.uppercaseMetadataKeys(sample_obj.get_metadata_json())
            # rename the sample_id field to sample_id_str cuz we use an int in our db for this field
            self.rename_sample_name(sample_metadata_json)            
            # seperate sample metadata by table
            sample_related_value_map = self.seperateMobedacMetadataByTable(sample_metadata_json, self.sample_related_metadata_map_json) 
            # now build up the update/insert
            sample_metadata_row_id = self.writeSampleMetadata(sample_related_value_map, detail.sample_id, detail.vamps_project_name, detail.vamps_dataset_name)
            # now write out the library metadata
            library_obj = LibraryORM.getFromMOBEDAC(detail.library_id, None, self.sess_obj)
            library_metadata_json = self.uppercaseMetadataKeys(library_obj.get_metadata_json())
            # seperate sequence/library metadata by table
            sequence_value_map = self.seperateMobedacMetadataByTable(library_metadata_json, self.sequence_related_metadata_map_json) 
            sequence_data = sequence_value_map["SEQUENCE_PREP"] # for now only one table in here for sequences...could be more later?
            # what are the key fields for the library/sequence:  vamps project, vamps dataset, sample id (our db id)           
            self.insertOrUpdateRow("SEQUENCE_PREP", sequence_data, {"SAMPLE_METADATA_ID" : {"value" : sample_metadata_row_id}, "VAMPS_PROJECT" : {"value" : detail.vamps_project_name}, "VAMPS_DATASET" : {"value" : detail.vamps_dataset_name} })
            
    
    # seperate mobedac metadata by table
    def seperateMobedacMetadataByTable(self, metadata_json, reference_map):
        # will write out a sample_metadata, common_flds tables...then specific sets depending on which type of sample
        # we have, human, plant, enviro etc.
        table_value_map = {}
        # loop over all of the input metadata and compare it against our configuration data of metadata fields and 
        # which db tables they belong to...that is in: metadata_map.py and you will find the qiime schema
        for metadata_field_name, metadata_value in metadata_json.items():
            table_name = self.find_field_in_map(metadata_field_name, reference_map)
            if table_name == None:
                # could not find this field in our map :o
                # should probably log an error message
                pass
            else:
                # found it so add it to our list of tables and fields
                self.accumulate_by_key(table_value_map, table_name, { metadata_field_name : metadata_value})
        return table_value_map
        
    # this routine writes out the metadata for the sample/library...this is divided among n tables
    # some of them are: sample_metadata, common_fields, host_associated_human, host_associated_plant, air, etc
    # each field name in the metadata (the mixs/mimarks ones) are unique so there is a python class metadata_map.py that has
    # a dictionary of table => fields and so that is used to find out which input metadata fields belong to which tables
    # so it is fairly data driven.  
    def writeSampleMetadata(self, table_value_map, sample_id, vamps_project, vamps_dataset):
        try:
            # should now have a dictionary that looks something like:
            # "SAMPLE_METADATA" : { 
            #      "SAMPLE_NAME" : {"value" : "2"},
            #      "PUBLIC"  : {"value" : "3"},
            #      "ASSIGNED_FROM_GEO"  : {"value" : "4"},
            #      "ALTITUDE" : {"value" : "5"}, ....  and so on and so on
            #  },
            # "COMMON_FIELDS" : {
            #      "ALKALINITY" : {"value" : "2"},
            #      "ALKYL_DIETHERS" : {"value" : "2.1"},
            #      "AMINOPEPT_ACT" : {"value" : "2.1"}, .... and so on
            #  and so on

            # write out the Sample table row...get the sub dictionary of those fields
            sample_data = table_value_map["SAMPLE_METADATA"]
            # what are the key fields for the sample:  vamps project, vamps dataset, mobedac sample id str            
            self.insertOrUpdateRow("SAMPLE_METADATA", sample_data, {"MOBEDAC_SAMPLE_ID" : {"value" : sample_id} })
            # now get the id of the sample object just INSERT'ed or UPDATE'd
            result_proxy = test_engine.execute("SELECT SAMPLE_METADATA_ID FROM SAMPLE_METADATA WHERE MOBEDAC_SAMPLE_ID='%s'" % (sample_id))
            sample_metadata_row_id = result_proxy.first()['SAMPLE_METADATA_ID']
            # first remove the sample one because we explicitly did that one first
            del table_value_map["SAMPLE_METADATA"]
                        
            # there are some other special tables to deal with...HOST and HOST_SAMPLE
            # this is a special case because the HOST_SUBJECT_ID is the mobedac name for the host
            # and in this qiime schema they create a matching object and tie the HOST and SAMPLE_METADATA together with the HOST_SAMPLE 
            # associattion table
            # is there the special HOST_SUBJECT_ID sent to us? if so then we know we have to do the host special processing
            host_data = table_value_map["HOST"]
            if(host_data != None):
                # we are dealing with a HOST data set
                # write out the HOST table row...get the sub dictionary of those fields
                
                # get the mobedac side name of this host
                host_subject_id = self.find_field_in_list("HOST_SUBJECT_ID", host_data)["value"]
                # what is the key field we'll use:  host_subject_id          
                self.insertOrUpdateRow("HOST", host_data, {"HOST_SUBJECT_ID" : {"value" : host_subject_id} })
                # now get the id of the host object just INSERT'ed or UPDATE'd
                result_proxy = test_engine.execute("SELECT host_id FROM HOST WHERE HOST_SUBJECT_ID='%s'" % (host_subject_id))
                host_metadata_row_id = result_proxy.first()['host_id']
                # now create or update the HOST_SAMPLE row
                self.insertOrUpdateRow("HOST_SAMPLE", table_value_map["HOST_SAMPLE"], 
                                       {  "HOST_ID" : {"value" : host_metadata_row_id},
                                          "SAMPLE_METADATA_ID" : {"value" : sample_metadata_row_id}  })
                # don't need these in the list anymore
                del table_value_map["HOST"]
                del table_value_map["HOST_SAMPLE"]
                        
            # so now we can simply loop over the other table name/field sets and write out the records for those
            for table_name, field_array in table_value_map.items():
                self.insertOrUpdateRow(table_name, field_array, {"SAMPLE_METADATA_ID" : {"value" : sample_metadata_row_id}})
            
            # finally write out the object that links the SAMPLE_METADATA to the VAMPS projects and datasets
            # this row has only foreign keys plus its own row id
            self.insertOrUpdateRow("VAMPS_PROJ_DS_SAMPLE_METADATA", {}, {"SAMPLE_METADATA_ID" : {"value" : sample_metadata_row_id},
                                                                         "VAMPS_PROJECT" : {'value' :vamps_project },
                                                                         "VAMPS_DATASET" : {'value' : vamps_dataset}})
            
            
            return sample_metadata_row_id
            
        except:
            self.log_exception("Some kind of error writing metadata")
            raise
            
    
    def insertOrUpdateRow(self, table_name, field_value_dict_array, key_maps):
        # does this exist already?
        where_clause = " and ".join([ key_field_name + "='" + str(key_value_dict["value"]) + "'"   for key_field_name,key_value_dict in key_maps.items() ])
        object_select_sql = "SELECT * FROM " + table_name + " WHERE " + where_clause
        self.log_debug("attempting to locate existing metadata object sql: " + object_select_sql)
        existing_result_proxy = test_engine.execute("SELECT * FROM " + table_name + " WHERE " + where_clause)
        # if we found the row using the key fields and we at least have some non key field values to UPDATE...then do the update else INSERT 
        if existing_result_proxy.first() and field_value_dict_array :
            # do an update
            set_str_array = [ field_value_dict.keys()[0] + "='" + str(self.getMetadataValue(field_value_dict.values()[0])) + "'"   for field_value_dict in field_value_dict_array ]
            set_str = ", ".join(set_str_array)
            sql = "UPDATE " + table_name + " set " + set_str +" WHERE " + where_clause
        else:
            # do a create
            # convert array of dictionary to just a dictionary of dictionaries
            # each of the dictionary has just 1 key/value the key is the field name and value is the metadata value, type etc
            entire_field_set_map = {}
            for field_dictionary in field_value_dict_array:
                field_name = field_dictionary.keys()[0]
                value = field_dictionary[field_name]
                entire_field_set_map[field_name] = value
            # now merge in the keys as well...we want to use those in the INSERT
            entire_field_set_map.update(key_maps)
            field_list = [field_name for field_name in entire_field_set_map.keys()]
            value_list =  [self.getMetadataValue(entire_field_set_map[field_name])   for field_name in field_list]
            sql = "INSERT " + table_name + " (" + ",".join([fld for fld in field_list]) + ") values (" + ",".join(["'"+str(val)+"'" for val in value_list]) + ")" 
        # now run it
        self.log_debug("attempting to INSERT/UPDATE metadata object sql: " + sql)
        result_proxy = test_engine.execute(sql)
        return result_proxy
        
    # for now value_obj could be a string or a dictionary with a 'value' : <the real value> entry
    # waiting for Mobedac to switch over to the "field name" : { 'value' : 'the value', 'type' : 'the type', ...other stuff } format
    def getMetadataValue(self, value_obj):
        if type(value_obj) is dict:
            return value_obj['value']
        else:
            return str(value_obj)
        
    def find_field_in_map(self, field_name, metadata_map):
        for table_name, field_map in metadata_map.items():
            field_entry = field_map.get(field_name, None)
            if field_entry != None:
                return table_name
        return None
    
    def find_field_in_list(self, field_name, field_map_array):
        for field_data_map in field_map_array:
            if field_data_map.get(field_name, None) != None:
                return field_data_map[field_name]
        return None
            
    # download the raw untrimmed sequence file from MOBEDAC and convert it
    # to Andy's clean fa format
    def download(self, submission, submissiondetail_array):
        for detail in submissiondetail_array:
            # lets make a dir for the data for this object  dir:  <root>/submission.id/submission_detail.id/
            processing_dir = self.create_submission_detail_processing_dir(submission, detail)

            sequence_set_id = detail.sequenceset_id  
            print "SSS: detail = %s, sequence_set_id = %s" % (detail, sequence_set_id)    
            # now get the sequence set as object? or just a file? how?
            try:
                # first download it
                file_type = self.download_raw_sequence_file(detail, sequence_set_id, processing_dir)
                # now convert it from raw format to clean fasta for VAMPS
                self.convert_sequence_file(file_type, processing_dir)
            except:
                self.log_to_submission_detail(detail, "Error retrieving sequence set: " + detail.sequenceset_id)
                return        
            # if all went ok with the download and conversion then mark this submission_detail as completed
            # the next step of work to do is UPLOAD to VAMPS
            detail.next_action = SubmissionDetailsORM.ACTION_VAMPS_UPLOAD
        # save all the modified detail objects in the cache to the db
        self.sess_obj.commit()

    # call back to MoBEDAC and get the sequence file....could take a long time
    def download_raw_sequence_file(self, detail, sequence_set_id, processing_dir):
        full_seq_file_download_url = ""
        remote_file_handle = None
        raw_seq_file = None
        print "SSS1: sequence_set_id = %s" % sequence_set_id    

        try:
            # get a connection to the file
            full_seq_file_download_url = "http://" + get_parm("mobedac_host") + get_parm("mobedac_base_path") + "sequenceSet/" + sequence_set_id + "?auth=" + get_parm("mobedac_auth_key")                
            self.log_debug("attempting download of seq file with url: " + full_seq_file_download_url)
            remote_file_handle = urllib2.urlopen(full_seq_file_download_url)                
            # is it fasta or what?
            # Tobi is putting the file type into the HTTP header
            response_headers = remote_file_handle.info().headers
            # assume this
            file_type = "fasta"
            valid_file_types = ["fasta", "fastq", "sff"]
            for h in response_headers:
                hlower = h.lower()
                idx = hlower.find("content-type:")
                if idx == 0:
                    file_type = hlower[(idx + len("content-type:")):].strip().replace("application/","")
                    break
            # if we didn't find a type we know then default it
            if file_type not in valid_file_types:
                file_type = "fasta"
            # now write out the raw file
            raw_seq_file_name = self.get_raw_sequence_file_name(file_type, processing_dir)
            # this could be an sff file? which would be binary
            binary_flag = "b" if file_type == "sff" else ""
            raw_seq_file = open(raw_seq_file_name, "w" + binary_flag)
            buffer_size=8192
            while 1:
                copy_buffer = remote_file_handle.read(buffer_size)
                if copy_buffer:
                    raw_seq_file.write(copy_buffer)
                else:
                    break
            self.log_debug("successfully downloaded seq file with url: " + full_seq_file_download_url)
            return file_type
        except:
            self.log_to_submission_detail(detail, "Error during retrieving of sequence data from MoBEDAC")
            raise
        finally:         
            if remote_file_handle != None:
                remote_file_handle.close()
            if raw_seq_file != None:
                raw_seq_file.close()
                
    def get_raw_sequence_file_name(self, file_type, processing_dir):
        return self.get_sequence_file_base_name(file_type, processing_dir) + "." + file_type

    def get_sequence_file_base_name(self, file_type, processing_dir):
        return os.path.join(processing_dir, Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX)

    # VAMPS wants a fa file in 'clean' format
    # convert from raw format to create clean file and possibly the quality file too
    def convert_sequence_file(self, file_type, processing_dir):
        raw_file_handle = None
        clean_seq_file_handle = None
        quality_file_handle = None
        try:
            # open the raw file
            raw_seq_file_name = self.get_raw_sequence_file_name(file_type, processing_dir)
            binary_flag = "b" if file_type == "sff" else ""
            raw_file_handle = open(raw_seq_file_name, "r" + binary_flag)
            # now open/create the clean file
            clean_seq_file_name = self.get_sequence_file_base_name(file_type, processing_dir) + ".fa"
            clean_seq_file_handle = open(clean_seq_file_name, 'w')
            generate_quality_file = (file_type != 'fasta')
            if generate_quality_file:
#                processing_dir = self.get_submission_processing_dir(submission)
                file_full_name = processing_dir + "/" + file_type + ".qual"
                quality_file_handle = open(file_full_name, 'w')
#                quality_file_handle = open(file_type + ".qual", 'w')
            # use the sff record id rather than trying to parse it with fasta/q
            use_seq_record_id = (file_type == 'sff') 
            self.log_debug("attempting to convert sequence file: " + raw_seq_file_name)
            self.log_debug("attempting to convert type: " + file_type)
            # parse and write out the clean files
            for seq_record in SeqIO.parse(raw_file_handle, file_type):
                if use_seq_record_id:
                    id = seq_record.id
                    remainder = seq_record.description
                else:
                    parts = seq_record.description.split('|')
                    id = parts[0]
                    remainder = "|".join(parts[1:])            
                clean_seq_file_handle.write(">%s\t%s\t%s\n" % (id, str(seq_record.seq) , remainder))
                if generate_quality_file:
                    quality_file_handle.write(">%s\n%s\n" % (id, seq_record.letter_annotations["phred_quality"]))
            self.log_debug("successfully converted sequence file: " + raw_seq_file_name)
        except:
            self.log_exception("Error converting raw sequence file to clean fasta format")
            raise
        finally:
            # now close up shop
            if raw_file_handle != None:
                raw_file_handle.close()
            if clean_seq_file_handle != None:
                clean_seq_file_handle.close()
            if quality_file_handle != None:
                quality_file_handle.close()
    
    # upload each detail object (a library=sequence file) at a time to VAMPS
    def vamps_upload(self, submission, submissiondetail_array):
        for detail in submissiondetail_array:
            self.vamps_upload_helper(submission, detail)
    
    # this routine does the upload to VAMPS for one submissiondetail object (which represents a single sequence file)
    def vamps_upload_helper(self, submission, submissiondetail):
        # get the project object from MOBEDAC
        # could have saved all of these projects, library objects here on the API side's db
        # but it is very quick to call over to MOBEDAC to retrieve their json data so we just do that
        # since this processing is taking place asynchronously on our dime
        try:
            project = ProjectORM.getFromMOBEDAC(submissiondetail.project_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission project: " + submissiondetail.project_id)
            return
        try:
            # get the Library from MOBEDAC
            library = LibraryORM.getFromMOBEDAC(submissiondetail.library_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission library: " + submissiondetail.library_id)
            self.log_exception("Upload to VAMPS, Error retrieving submission library: " + submissiondetail.library_id)
            return

        try:            
            # possible errors to check for
            # check vamps_upload_info and vamps_project_info for duplicate project/dataset combos
            # need generated project name, dataset name         
            #
            # this routine will create the primer, key, param files and then submit      
            submissiondetail.vamps_status_record_id = self.create_files_and_upload(submission, submissiondetail, project, library)
    
            # if all went ok then mark this as completed
            submissiondetail.next_action = SubmissionDetailsORM.ACTION_GAST
            # save it
            self.sess_obj.commit()
        except:
            self.log_to_submission(submission, "Error during preparation and UPLOAD to VAMPS")
            self.log_exception("Error during preparation and UPLOAD to VAMPS: ")
                
    # need to create 4 files to upload to VAMPS
    # sequence file, run key file, primer file and params file
    def create_files_and_upload(self, submission, submission_detail, project, library_obj): 
        processing_dir = os.path.join(self.create_submission_detail_processing_dir(submission, submission_detail),"")

        # now create the primer file
        # first get the owning Library
        primers = library_obj.get_primers()
        primer_file_name = processing_dir + "primers.txt"
        self.create_primer_file(primers, primer_file_name)
        
        # now create the key file
        run_key = library_obj.get_run_key()
        key_hash = {"key" : run_key, "direction" : library_obj.get_direction(),
                    "region" : submission_detail.region, "project" : submission_detail.vamps_project_name, "dataset" : submission_detail.vamps_dataset_name}
        run_key_file_name = processing_dir + "run_key.txt"
        print "run_key_file_name (%s) = processing_dir (%s) + run_key.txt" % (run_key_file_name, processing_dir)

        self.write_run_key_file(run_key_file_name, key_hash)
        
        # create the param file
        param_file_name = processing_dir + "params.prm"
        self.create_params_file(param_file_name, submission.user, run_key, project.description[0:255], "Dataset description test", project.name)
        
        # now send the files on up
        vamps_status_record_id = self.upload_to_vamps(submission_detail, processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX, primer_file_name, run_key_file_name, param_file_name)
        return vamps_status_record_id
    
    # check with Andy on what he wants for this
    def create_params_file(self, param_file_name, vamps_user, run_key, project_description, dataset_description, project_title):
        param_file_name
        params_file = open(param_file_name, 'w')
        params_file.write("username=%s\n" % (vamps_user))
        params_file.write("time=%s\n" % ('daytime'))
        params_file.write("platform=%s\n" % ('454'))  # need to get this somewhere
        params_file.write("%s:description=%s\n" % (run_key,dataset_description))
        params_file.write("env_source=%s\n" % ('marine'))  # neeed to get this from somewhere
        params_file.write("project_description=%s\n" % (project_description))
        params_file.write("project_title=%s\n" % (project_title))
        params_file.flush()
        params_file.close()

    # generate the run key file...format of this can be found in the Upload section on the VAMPS website
    def write_run_key_file(self, run_key_file_name, key_hash):
        run_key_file_name
        key_file = open(run_key_file_name, 'w')
        key_line = Template("$key\t$direction\t$region\t$project\t$dataset\n").substitute(key_hash)
        key_file.write(key_line)
        key_file.close()
        
    # generate the primer file...format of this can be found in the Upload section on the VAMPS website    
    def create_primer_file(self, primer_array, primer_file_name):
        primer_file_name
        primer_file = open(primer_file_name, 'w')
        p_index = 0
        for primer in primer_array:
            # force in some defaults...maybe mobedac won't have them
            primer["name"] = primer.get("name", "p_" + str(p_index))
#            primer["location"] = primer.get("location", "p_" + str(p_index))
            primer_line = Template("$name\t$direction\t$sequence\t$regions\t$location\n").substitute(primer)
#            print "PPP primer_line = " % (primer_line)
            primer_file.write(primer_line)
            p_index += 1
        primer_file.close()
            
    def upload_to_vamps(self, submission_detail, sequence_file_name_prefix, primer_file_name, run_key_file_name, param_file_name):
        response = None
        try:
            # headers contains the necessary Content-Type and Content-Length
            # datagen is a generator object that yields the encoded parameters
            # VAMPS expects 4 or 5 files in this multipart form upload they have the parameter names shown below
            post_params = {
                         'seqfile'   : open(sequence_file_name_prefix + ".fa","r"),
                         'primfile'  : open(primer_file_name,"r"),
                         'keyfile'   : open(run_key_file_name,"r"),
                         'paramfile' : open(param_file_name,"r")
                         }
            # where to send it?
            vamps_upload_url = get_parm('vamps_data_post_url')
            # do we also send a qual file? if one was generated then we should send it
            possible_qual_file_name = sequence_file_name_prefix + ".qual"
            if os.path.exists(possible_qual_file_name):
                vamps_upload_url = get_parm('vamps_data_post_url_with_qual_file')
                post_params['qualfile'] = open(possible_qual_file_name,"r")
            
            datagen, headers = encode.multipart_encode(post_params)
            # Create the Request object
            request = urllib2.Request(vamps_upload_url, datagen, headers)
            # Actually do the POST to VAMPS, and get the response
            response = urllib2.urlopen(request)
            if response.code != 200:
                raise "Error uploading sequence files to VAMPS: " + response.msg
            # this response string is very important because if things were successful then it holds
            # the id of the vamps status record that we will need in our processing
            response_str = response.read()
            self.log_debug("Successfully uploaded to VAMPS submission_detail: " + str(submission_detail.id) + " got response id: " + response_str)
            return response_str
        except:
            self.log_exception("Error connecting with VAMPS processor to upload submission_detail: " + str(submission_detail.id))
            raise
        finally:
            if response != None:
                response.close()
            pass

