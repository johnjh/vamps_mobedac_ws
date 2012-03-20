#!/usr/bin/python
import cherrypy
import threading
import time
from submissionorm import SubmissionORM
from sequencesetorm import SequenceSetORM
from projectorm import ProjectORM
from sampleorm import SampleORM
from libraryorm import LibraryORM
import json as json
from Bio import SeqIO
import os
import datetime
from string import Template
from rest_log import mobedac_logger
import shutil
from poster import streaminghttp 
from poster import encode
import urllib2, urllib
from urllib2 import URLError, HTTPError
from sqlalchemy import *
from sqlalchemy import  and_
from dbconn import Session,vampsSession
import sys
import traceback
from initparms import get_parm
from submission_detailsorm import SubmissionDetailsORM
import httplib


class Submission_Processor (threading.Thread):
    MOBEDAC_SEQUENCE_FILE_NAME = "mobedac_sequences.seq"
    MOBEDAC_SEQUENCE_FILE_NAME_PREFIX = "mobedac_sequences"
    
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
        
        threading.Thread.__init__(self)
     
    def log_debug(self, msg):
        mobedac_logger.debug("submission processor: " + msg)
        
    def log_info(self, msg):
        mobedac_logger.info("submission processor: " + msg)

    def log_exception(self, msg):
        mobedac_logger.exception("submission processor: " + msg)
        
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
        
    def create_submission_processing_dir(self, submission):
        processing_dir = self.root_dir + "/" + str(submission.id)
        if os.path.exists(processing_dir) == False:
            os.mkdir(processing_dir)
        return processing_dir

    def create_submission_detail_processing_dir(self, submission, submissiondetail):
        processing_dir = self.create_submission_processing_dir(submission) + "/" + str(submissiondetail.id) 
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
                self.log_debug("top of processing loop woke up from sleep...processing=TRUE")
                if self.exitFlag:
                    return;
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_DOWNLOAD)
                if self.exitFlag:
                    return;
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_VAMPS_UPLOAD)
                if self.exitFlag:
                    return;
                self.perform_action_on_submissions(SubmissionDetailsORM.ACTION_GAST)
                if self.exitFlag:
                    return;
                self.return_results_to_mobedac()
                if self.exitFlag:
                    return;

    # see if there are any complete sets of submission details 
    # that we can process and perhaps generate the tax table and return that to MoBEDAC
    def return_results_to_mobedac(self):
        self.sess_obj = None
        try:
            self.sess_obj = Session()
            details_hashed_by_submission_id = {}
                
            # get all submission detail objects that have a status of 'post_results_to_mobedac'
            for detail in self.sess_obj.query(SubmissionDetailsORM).filter(SubmissionDetailsORM.next_action == SubmissionDetailsORM.ACTION_POST_RESULTS_TO_MOBEDAC).all():
                detailed_array_by_submission_id = details_hashed_by_submission_id.get(detail.submission_id, None)
                if detailed_array_by_submission_id == None:
                    details_hashed_by_submission_id[detail.submission_id] = []
                details_hashed_by_submission_id[detail.submission_id].append(detail)
                
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
                    status_row = detail.get_VAMPS_submission_status_row(self.sess_obj)
                    if status_row == None:
                        raise "Error locating vamps_upload_status record found for submission_detail: " + detail.id + " vamps_status_id: " + str(detail.vamps_status_record_id)
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
                # find out the user
                submission = SubmissionORM.get_instance(key, self.sess_obj)
                taxonomy_table_json = self.get_taxonomy_table(project_count, sampleOrderNames, submission.user, 'family')
                if taxonomy_table_json == None:
                    continue
                # send the tax table to mobedac
                success = self.send_to_mobedac(submission, library_ids, details_by_library_id, taxonomy_table_json)
                # if all went well then mark all the details as complete
                if(success):
                    for detail in value:
                        detail.next_action = SubmissionDetailsORM.ACTION_PROCESSING_COMPLETE
                    self.sess_obj.commit()
        except:
            self.log_exception("Got exception during taxonomy generation and mobedac sending")
        
    def get_analysis_links(self, user, details_by_library_id):
        links = {}
        for library, detail in details_by_library_id.items():
            links[library] = {"Visualization" : get_parm('vamps_landing_page_str') % (detail.vamps_project_name, user) }
        return links
    
    # post the analysis results back to MoBEDAC
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
            req = urllib2.Request(mobedac_results_url, json.dumps(results_dict), { 'Content-Type' : 'application/json' })
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
            
    # perform the action on the submissions in the db
    def perform_action_on_submissions(self, action):
        self.sess_obj = None
        try:
            self.sess_obj = Session()
            details_hashed_by_submission_id = {}
                
            # get all pending submission detail objects and put them in a hash where each key is the submission id
            # and each value is an array of detail objects
            for detail in self.sess_obj.query(SubmissionDetailsORM).filter(SubmissionDetailsORM.next_action == action).all():
                detailed_array_by_submission_id = details_hashed_by_submission_id.get(detail.submission_id, None)
                if detailed_array_by_submission_id == None:
                    details_hashed_by_submission_id[detail.submission_id] = []
                details_hashed_by_submission_id[detail.submission_id].append(detail)
                
            # now loop over all the arrays of detail objects
            final_detail_hashs_by_submission_id = {}
            for key, value in  details_hashed_by_submission_id.items():
                # value is now an array of detail objects all tied to its parent submission object id
                # we want to now group these by project name
                hashed_detail_objects = {}
                for detail in value:
                    details_by_project_name = hashed_detail_objects.get(detail.vamps_project_name, None)
                    if details_by_project_name == None:
                        hashed_detail_objects[detail.vamps_project_name] = []
                    hashed_detail_objects[detail.vamps_project_name].append(detail)
                final_detail_hashs_by_submission_id[key] = hashed_detail_objects
                
            # now we have a hash with key=submission id and the value is now a hash which is keyed by project name and the value is all details with that project name
            for submission_id, details_hash_by_project_name in final_detail_hashs_by_submission_id.items():
                # now get the items from the sub hash
                details_hash = details_hash_by_project_name
                for detail_array in details_hash.itervalues():
                    print "Working on submission details objects: " + str(detail_array)
                    # get the submission object
                    submission = self.sess_obj.query(SubmissionORM).filter(SubmissionORM.id == submission_id).one()
                    # make sure the base processing dir is there
                    self.create_submission_processing_dir(submission)
                    if self.exitFlag:
                        return;
                    try:
                        # assume all is well with these submission detail object(s)
                        self.clear_submission_msg_text(detail_array)
                        # find the action
                        action_method = getattr(self, action)
                        # do the action
                        action_method(submission, detail_array)
                    except:
                        self.log_exception("Got exception action: " + action + " processing submission id: " + str(submission.id))
        except:
            self.log_exception("error performing action on submission")
        finally:
            self.sess_obj.close()
            self.sess_obj = None
                
    def gast(self, submission, submissiondetail_array):
        response = None
        try:
            # so we can have a collection of submissions to gast
            # if there are more than 1 details in a project then we want to gast them as a group
            # and so they all have to be at the state of TRIM_SUCCESS else we can't gast yet
            for detail in submissiondetail_array:                          
                status_row = detail.get_VAMPS_submission_status_row(self.sess_obj)
                if status_row == None:
                    raise "Error preparing for GAST no vamps_upload_status record found for submission_detail: " + detail.id + " vamps_status_id: " + str(submission.vamps_status_record_id)
                if status_row[0] != self.VAMPS_TRIM_SUCCESS:
                    self.log_debug("Can't GAST submissiondetail: " + str(detail.id) + " yet, VAMPS status is: " + status_row[0])
                    return
            # if we land here then all submission detail objects in this project were uploaded and trimmed successfully and are waiting to be GASTed
            
            # can use just a single detail object because we GAST all the datasets in the project
            detail =  submissiondetail_array[0]
            values = {'project' : detail.vamps_project_name,
                      'new_source' : detail.region, 
                      'gast_ok' : '1',
                      'run_number' : detail.vamps_status_record_id
                      }
            
            data = urllib.urlencode(values)
            # Create the Request object
            request = urllib2.Request(self.vamps_gast_url, data)
            # Actually do the request, and get the response
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
         
    def download(self, submission, submissiondetail_array):
        for detail in submissiondetail_array:
            # lets make a dir for the data for this object  dir:  <root>/submission.id/submission_detail.id/
            processing_dir = self.create_submission_detail_processing_dir(submission, detail)

            sequence_set_id = detail.sequenceset_id      
            # now get the sequence set as object? or just a file? how?
            try:
                # first download it
                file_type = self.download_raw_sequence_file(detail, sequence_set_id, processing_dir)
                # now convert it from raw format to clean fasta for VAMPS
                self.convert_sequence_file(file_type, processing_dir)
            except:
                self.log_to_submission_detail(detail, "Error retrieving sequence set: " + detail.sequenceset_id)
                return        
            # if all went ok then mark this as completed
            detail.next_action = SubmissionDetailsORM.ACTION_VAMPS_UPLOAD
        # save it
        self.sess_obj.commit()

    # call back to MoBEDAC and get the sequence file....could take a long time
    def download_raw_sequence_file(self, detail, sequence_set_id, processing_dir):
        full_seq_file_download_url = ""
        remote_file_handle = None
        raw_seq_file = None
        try:
            # get a connection to the file
            full_seq_file_download_url = "http://" + get_parm("mobedac_host") + get_parm("mobedac_base_path") + "sequenceSet/" + sequence_set_id + "?auth=" + get_parm("mobedac_auth_key")                
            self.log_debug("attempting download of seq file with url: " + full_seq_file_download_url)
            remote_file_handle = urllib2.urlopen(full_seq_file_download_url)                
            # is it fasta or what?
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
            if file_type not in valid_file_types:
                file_type = "fasta"
            # now write out the raw file
            raw_seq_file_name = self.get_raw_sequence_file_name(file_type, processing_dir)
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
        return processing_dir + "/" +  Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX

    # convert from raw format and create clean file and possibly the quality file too
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
                quality_file_handle = open(file_type + ".qual", 'w')
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
        
    def vamps_upload(self, submission, submissiondetail_array):
        for detail in submissiondetail_array:
            self.vamps_upload_helper(submission, detail)
            
    def vamps_upload_helper(self, submission, submissiondetail):
        # start downloading from MoBEDAC
        # get the project object
        try:
            project = ProjectORM.get_remote_instance(submissiondetail.project_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission project: " + submissiondetail.project_id)
            return
        try:
            library = LibraryORM.get_remote_instance(submissiondetail.library_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission library: " + submissiondetail.library_id)
            self.log_exception("Upload to VAMPS, Error retrieving submission library: " + submissiondetail.library_id)
            return

        try:            
            # possible errors to check for
            # check vamps_upload_info and vamps_project_info for duplicate project/dataset combos
            # need generated project name, dataset name               
            submissiondetail.vamps_status_record_id = self.create_and_upload(submission, submissiondetail, project, library)
    
            # if all went ok then mark this as completed
            submissiondetail.next_action = SubmissionDetailsORM.ACTION_GAST
            # save it
            self.sess_obj.commit()
        except:
            self.log_to_submission(submission, "Error during preparation and UPLOAD to VAMPS")
            self.log_exception("Error during preparation and UPLOAD to VAMPS: ")
                
    # need to create 4 files to upload to VAMPS
    # sequence file, run key file, primer file and params file
    def create_and_upload(self, submission, submission_detail, project, library_obj): 
        processing_dir = self.create_submission_detail_processing_dir(submission, submission_detail) + "/"

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
        self.write_run_key_file(run_key_file_name, key_hash)
        
        # create the param file
        param_file_name = processing_dir + "params.prm"
        self.create_params_file(param_file_name, submission.user, run_key, project.description[0:255], "Dataset description test", project.name)
        
        # now send the files on up
        vamps_status_record_id = self.post_sequence_data(submission_detail, processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX, primer_file_name, run_key_file_name, param_file_name)
        return vamps_status_record_id
    
    def create_params_file(self, param_file_name, vamps_user, run_key, project_description, dataset_description, project_title):
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

        
    def post_sequence_data(self, submission_detail, sequence_file_name_prefix, primer_file_name, run_key_file_name, param_file_name):
        response = None
        try:
            # headers contains the necessary Content-Type and Content-Length
            # datagen is a generator object that yields the encoded parameters
            # VAMPS expects 4 or 5 files in this multipart form upload they have the parameter names shown below
            post_params = {
                         'seqfile' : open(sequence_file_name_prefix + ".fa","r"),
                         'primfile' : open(primer_file_name,"r"),
                         'keyfile' :open(run_key_file_name,"r"),
                         'paramfile' : open(param_file_name,"r")
                         }
            # where to send it?
            vamps_upload_url = get_parm('vamps_data_post_url')
            # do we also send a qual file? if one was generated they we should do it
            possible_qual_file_name = sequence_file_name_prefix + ".qual"
            if os.path.exists(possible_qual_file_name):
                vamps_upload_url = get_parm('vamps_data_post_url_with_qual_file')
                post_params['qualfile'] = open(possible_qual_file_name,"r")
            
            datagen, headers = encode.multipart_encode(post_params)
            # Create the Request object
            request = urllib2.Request(vamps_upload_url, datagen, headers)
            # Actually do the request, and get the response
            response = urllib2.urlopen(request)
            if response.code != 200:
                raise "Error uploading sequence files to VAMPS: " + response.msg
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

    
    def write_run_key_file(self, run_key_file_name, key_hash):
        key_file = open(run_key_file_name, 'w')
        key_line = Template("$key\t$direction\t$region\t$project\t$dataset\n").substitute(key_hash)
        key_file.write(key_line)
        key_file.close()
        
        
    def create_primer_file(self, primer_array, primer_file_name):
        primer_file = open(primer_file_name, 'w')
        p_index = 0
        for primer in primer_array:
            # force in some defaults...maybe mobedac won't have them
            primer["name"] = primer.get("name", "p_" + str(p_index))
            primer["location"] = primer.get("location", "p_" + str(p_index))
            primer_line = Template("$name\t$direction\t$sequence\t$regions\t$location\n").substitute(primer)
            primer_file.write(primer_line)
            p_index += 1
        primer_file.close()
    