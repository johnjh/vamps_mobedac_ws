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
from sqlalchemy import *
from dbconn import Session,vampsSession
import sys
import traceback
from initparms import get_parm
from submission_detailsorm import SubmissionDetailsORM
import urllib2


class Submission_Processor (threading.Thread):
    MOBEDAC_SEQUENCE_FILE_NAME = "mobedac_sequences.seq"
    MOBEDAC_SEQUENCE_FILE_NAME_PREFIX = "mobedac_sequences"
    
    # some VAMPS processing code
    VAMPS_TRIM_SUCCESS = "TRIM_SUCCESS"
    
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
        
    def log_exception(self, msg):
        mobedac_logger.exception("submission processor: " + msg)
        
    def stop_processing(self):   
        self.exitFlag = True
        
    def disable_processing(self):   
        self.halt_processing = True
        
    def enable_processing(self):   
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
            self.log_debug("top of processing loop about to sleep")
            # sleep 30 seconds...this should be parameterized
            time.sleep(30)
            if self.halt_processing == False:
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
                    base_dir = self.create_submission_processing_dir(submission)
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
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.sess_obj.close()
            self.sess_obj = None
            
    def gast(self, submission, submissiondetail_array):
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
                detail.next_action = SubmissionDetailsORM.ACTION_GAST_COMPLETE
            self.sess_obj.commit()
        except:
            self.log_exception("Some kind of error preparing to or actually calling VAMPS to GAST")
            self.log_to_submission(submission, "Some kind of error preparing to or actually calling VAMPS to GAST")
            raise
         
    def download(self, submission, submissiondetail_array):
        for detail in submissiondetail_array:
            # lets make a dir for the data for this object  dir:  <root>/submission.id/submission_detail.id/
            processing_dir = self.create_submission_detail_processing_dir(submission, detail)

            sequence_set = SequenceSetORM.get_remote_instance(detail.sequenceset_id, None, self.sess_obj)      
            # now get the sequence set as object? or just a file? how?
            try:
                self.download_sequence_file(detail, sequence_set, processing_dir)
            except:
                self.log_to_submission_detail(detail, "Error retrieving sequence set: " + detail.sequenceset_id)
                return        
            # if all went ok then mark this as completed
            detail.next_action = SubmissionDetailsORM.ACTION_VAMPS_UPLOAD
        # save it
        self.sess_obj.commit()

    # call back to MoBEDAC and get the sequence file....could take a long time
    def download_sequence_file(self, detail, sequence_set, processing_dir):
        try:
            # dev mode?
            if get_parm("remote_objects_are_local").lower() == 'true':
                # this will eventually be a URL on mobedac that should get us a stream object?
                mobedac_file_path = get_parm("test_sequence_file_path") + sequence_set.id + ".fa"
                mobedac_file = open(mobedac_file_path, "r")
                raw_seq_file_name = Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME
                raw_seq_file = open(processing_dir + "/" + raw_seq_file_name, 'w')
                buffer_size=8192
                while 1:
                    copy_buffer = mobedac_file.read(buffer_size)
                    if copy_buffer:
                        raw_seq_file.write(copy_buffer)
                    else:
                        break
                mobedac_file.close()
                raw_seq_file.close()
            else:
                # open the sequence set file on mobedac and try to download it
                mobedac_file = urllib2.urlopen(sequence_set.sequences) 
                raw_seq_file_name = Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME
                raw_seq_file = open(processing_dir + "/" + raw_seq_file_name, 'w')
                buffer_size=8192
                while 1:
                    copy_buffer = mobedac_file.read(buffer_size)
                    if copy_buffer:
                        raw_seq_file.write(copy_buffer)
                    else:
                        break
                mobedac_file.close()
                raw_seq_file.close()
        except:
            self.log_to_submission_detail(detail, "Error during retrieving of sequence data from MoBEDAC")
            raise
        
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
            sample = SampleORM.get_remote_instance(submissiondetail.sample_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission sample: " + submissiondetail.sample_id)
            return
        
        try:
           library = LibraryORM.get_remote_instance(submissiondetail.library_id, None, self.sess_obj)
        except:
            self.log_to_submission_detail(submissiondetail, "Upload to VAMPS, Error retrieving submission library: " + submissiondetail.library_id)
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
        
        
    # need to create 4 files to upload to VAMPS
    # sequence file, run key file, primer file and params file
    def create_and_upload(self, submission, submission_detail, project, library_obj): 
        processing_dir = self.create_submission_detail_processing_dir(submission, submission_detail) + "/"

        # now create the cleaned seq file
        # create the cleaned sequence file also
        clean_sequence_file_name = processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX + "_clean.fa"
        self.convert_raw_to_clean_seq(str(submission_detail.id), processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME, Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX, clean_sequence_file_name)

        # now create the primer file
        # first get the owning Library
        primers = json.loads(library_obj.primers)
        primer_file_name = processing_dir + "primers.txt"
        self.create_primer_file(primers, primer_file_name)
        
        # now create the key file
        run_key = library_obj.run_key
        key_hash = {"key" : run_key, "direction" : library_obj.direction,
                    "region" : submission_detail.region, "project" : submission_detail.vamps_project_name, "dataset" : submission_detail.vamps_dataset_name}
        run_key_file_name = processing_dir + "run_key.txt"
        self.write_run_key_file(run_key_file_name, key_hash)
        
        # create the param file
        param_file_name = processing_dir + "params.prm"
        self.create_params_file(param_file_name, submission.user, run_key, project.description[0:255], "Dataset description test", project.name)
        
        # now send the files on up
        vamps_status_record_id = self.post_sequence_data(submission_detail, clean_sequence_file_name, primer_file_name, run_key_file_name, param_file_name)
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

        
    def post_sequence_data(self, submission_detail, clean_sequence_file_name, primer_file_name, run_key_file_name, param_file_name):
        try:
            # headers contains the necessary Content-Type and Content-Length
            # datagen is a generator object that yields the encoded parameters
            # VAMPS expects 4 or 5 files in this multipart form upload they have the parameter names shown below
            datagen, headers = encode.multipart_encode({
                                                 'seqfile' : open(clean_sequence_file_name,"r"),
                                                 'primfile' : open(primer_file_name,"r"),
                                                 'keyfile' :open(run_key_file_name,"r"),
                                                 'paramfile' : open(param_file_name,"r")
                                                 })
            # Create the Request object
            request = urllib2.Request(self.vamps_upload_url, datagen, headers)
            # Actually do the request, and get the response
            response = urllib2.urlopen(request)
            if response.code != 200:
                raise "Error uploading sequence files to VAMPS: " + response.msg
            response_str = response.read()
            self.log_debug("Uploaded to VAMPS submission_detail: " + str(submission_detail.id) + " got response id: " + response_str)
            return response_str
        except:
            self.log_exception("Error connecting with VAMPS processor to upload submission_detail: " + str(submission_detail.id))
            raise
        finally:
            pass
    
    def write_run_key_file(self, run_key_file_name, key_hash):
        key_file = open(run_key_file_name, 'w')
        key_line = Template("$key\t$direction\t$region\t$project\t$dataset\n").substitute(key_hash)
        key_file.write(key_line)
        key_file.close()
        
    def convert_raw_to_clean_seq(self, unique_key, raw_seq_file_name, raw_seq_file_name_prefix, clean_seq_file_name):
        raw_seq_file = open(raw_seq_file_name, 'r')
        clean_seq_file = open(clean_seq_file_name, 'w')
        for seq_record in SeqIO.parse(raw_seq_file, "fasta"):
            parts = seq_record.description.split('|')
            id = parts[0]
            remainder = "|".join(parts[1:])
            clean_seq_file.write(">%s\t%s\t%s\n" % (id, seq_record.seq, remainder))
            
        raw_seq_file.close()
        clean_seq_file.close()
        
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
    