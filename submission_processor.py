#!/usr/bin/python
import cherrypy
import threading
import time
from submissionorm import SubmissionORM
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

        threading.Thread.__init__(self)
     
    def log_debug(self, msg):
        mobedac_logger.debug("submission processor: " + msg)
        
    def log_exception(self, msg):
        mobedac_logger.exception("submission processor: " + msg)
        
    def stop_processing(self):   
        self.exitFlag = True
        
    def run(self):
        # Register the streaming http handlers with urllib2
        streaminghttp.register_openers()
        # start the work
        while True:
            if self.exitFlag:
                return;
            self.perform_action_on_submissions(SubmissionORM.ACTION_DOWNLOAD)
            if self.exitFlag:
                return;
            self.perform_action_on_submissions(SubmissionORM.ACTION_VAMPS_UPLOAD)
            if self.exitFlag:
                return;
            self.perform_action_on_submissions(SubmissionORM.ACTION_GAST)
            if self.exitFlag:
                return;
            # sleep 30 seconds...this should be parameterized
            time.sleep(30)

    # perform the action on the submissions in the db
    def perform_action_on_submissions(self, action):
        self.sess_obj = None
        try:
            self.sess_obj = Session()
            # get all pending submissions
            for submission in self.sess_obj.query(SubmissionORM).filter(SubmissionORM.next_action == action).all():
                print "GOT a submission object id: " + str(submission.id)
                if self.exitFlag:
                    return;
                try:
                    # assume all is well with this submission object
                    self.clear_submission_msg_text(submission)
                    # find the action
                    action_method = getattr(self, action)
                    # do the action
                    action_method(submission)
                except:
                    self.log_exception("Got exception action: " + action + " processing submission id: " + str(submission.id))
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.sess_obj.close()
            self.sess_obj = None
            
    def gast(self, submission):
        try:
            # need to see if this submission whose next processing step is supposed to be GAST
            # is really ready for GASTing in the VAMPS system....because VAMPS might still be performing
            # all of the trimming work
            status_row = submission.get_VAMPS_submission_status_row(self.sess_obj)
            if status_row == None:
                raise "Error preparing for GAST of submission: " + str(submission.id) + " no vamps_upload_status record found for id: " + str(submission.vamps_status_record_id)
            if status_row[0] != self.VAMPS_TRIM_SUCCESS:
                self.log_debug("Can't GAST submission: " + str(submission.id) + " yet, VAMPS status is: " + status_row[0])
                return
             
            values = {'project' : submission.vamps_project_name,
                      'dataset' : submission.vamps_dataset_name,
                      'new_source' : submission.region, 
                      'gast_ok' : '1',
                      'run_number' : submission.vamps_status_record_id
                      }
            
            data = urllib.urlencode(values)
            # Create the Request object
            request = urllib2.Request(self.vamps_gast_url, data)
            # Actually do the request, and get the response
            response = urllib2.urlopen(request)
            if response.code != 200:
                raise "Error starting GAST processing in VAMPS: " + response.msg
            submission.next_action = SubmissionORM.ACTION_GAST_COMPLETE
            self.sess_obj.commit()
        finally:
            pass
         
    def log_to_submission(self, submission, msg):
        self.log_exception(msg)
        submission.current_status_msg = msg
        self.sess_obj.commit()

    def clear_submission_msg_text(self, submission):
        submission.current_status_msg = None
        self.sess_obj.commit()
        
        
    def download(self, submission):
        # lets make a dir for the data for this object
        processing_dir = self.root_dir + "/" + str(submission.id) + "/"
        if os.path.exists(processing_dir) == False:
            os.mkdir(processing_dir)
        
        # start downloading from MoBEDAC
        # get the project object
        try:
            project = ProjectORM.get_remote_instance(submission.project, None, self.sess_obj)
        except:
            self.log_to_submission(submission, "Error retrieving submission project: " + submission.project)
            return

        try:
#            sample = SampleORM.get_remote_instance(submission.sample, None, self.sess_obj)
            pass
        except:
            self.log_to_submission(submission, "Error retrieving submission sample: " + submission.sample)
            return
        
        try:
#           library = LibraryORM.get_remote_instance(submission.library, None, self.sess_obj)
            pass
        except:
            self.log_to_submission(submission, "Error retrieving submission library: " + submission.library)
            return

        # now get the sequence set as object? or just a file? how?
        try:
            self.download_sequence_file(submission, processing_dir)
        except:
            self.log_to_submission(submission, "Error retrieving sequence set: " + submission.sequence_set)
            return
        
        # if all went ok then mark this as completed
        submission.next_action = SubmissionORM.ACTION_VAMPS_UPLOAD
        submission.current_status_msg = "Data successfully downloaded from MoBEDAC server...transferring to VAMPS processor"
        # save it
        self.sess_obj.commit()
        
        
    def vamps_upload(self, submission):
        # start downloading from MoBEDAC
        # get the project object
        try:
            project = ProjectORM.get_remote_instance(submission.project, None, self.sess_obj)
        except:
            self.log_to_submission(submission, "Upload to VAMPS, Error retrieving submission project: " + submission.project)
            return

        try:
            sample = SampleORM.get_remote_instance(submission.sample, None, self.sess_obj)
        except:
            self.log_to_submission(submission, "Upload to VAMPS, Error retrieving submission sample: " + submission.sample)
            return
        
        try:
#           library = LibraryORM.get_remote_instance(submission.library, None, self.sess_obj)
            pass
        except:
            self.log_to_submission(submission, "Upload to VAMPS, Error retrieving submission library: " + submission.library)
            return

        try:
            library = LibraryORM({})
            library_json_data = {
             "run_key" : "GACAG",  
             "direction" : "F",  
             "region" : "v6",
             "primers" : [
    {"name" : "967F",    "direction" : "F",    "sequence" : "CNACGCGAAGAACCTTANC",   "regions" : "v6",   "location" : "967F"},
    {"name" : "967F-UC1",   "direction" :  "F",  "sequence" :   "CAACGCGAAAA+CCTTACC",   "regions" :  "v6",    "location" :  "967F"},
    {"name" : "967F-UC2",   "direction" :  "F" ,  "sequence" :  "CAACGCGCAGAACCTTACC",   "regions" :  "v6",    "location" :  "967F"},
    {"name" : "967F-UC3",   "direction" :  "F",    "sequence" : "ATACGCGA[AG]GAACCTTACC",  "regions" :   "v6",    "location" :  "967F"},
    {"name" : "967F-UC4",   "direction" :  "F",   "sequence" :  "CTAACCGANGAACCTYACC" ,  "regions" :  "v6",   "location" :   "967F"},
    {"name" : "967F-PP",   "direction" :  "F" ,  "sequence" :  "C.ACGCGAAGAACCTTA.C",   "regions" :  "v6",    "location" :  "967F"},
    {"name" : "967F-AQ",  "direction" :   "F",   "sequence" :  "CTAACCGA.GAACCT[CT]ACC",   "regions" :  "v6",    "location" :  "967F"},
    {"name" : "1046R",    "direction" : "R",   "sequence" :  "AGGTG.?TGCATGG*CTGTCG",   "regions" :  "v6",    "location" :  "1046R"},
    {"name" : "1046R-PP",   "direction" :  "R" ,  "sequence" :  "AGGTG.?TGCATGG*TTGTCG",   "regions" :  "v6",    "location" :  "1046R"},
    {"name" : "1046R-AQ1",   "direction" :  "R",   "sequence" :  "AGGTG.?TGCATGG*CCGTCG",  "regions" :  "v6",    "location" :  "1046R"},
    {"name" : "1046R-AQ2",   "direction" :  "R",   "sequence" :  "AGGTG.?TGCATGG*TCGTCG",   "regions" :  "v6",    "location" :  "1046R" }                      
                          ]}
            library.primers = json.dumps(library_json_data["primers"])
            library.direction = library_json_data['direction']
            library.region = library_json_data['region']
            library.run_key = library_json_data['run_key']
            
            library.region = library.region.lower()
            option_json = json.loads(submission.options)
    #        project_code = option_json["project_name_code"]
            project_code = "JJH_"
            # project name is <project_code>_<domain><region>
            # and the <project_code> should be of the format like <4 letter project abbreviation>_<PI INITIALS>
            final_project_code = project_code + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + option_json['domain'][0].upper() + library.region
      
            # get the sequence set name
            sequence_set_name = "test_set"  # this should eventually be the .name field of the sequence set object retrieved from MoBEDAC
            
            # possible errors to check for
            # check vamps_upload_info and vamps_project_info for duplicate project/dataset combos
            # need generated project name, dataset name               
            submission.vamps_status_record_id = self.create_and_upload(submission, sequence_set_name, final_project_code, project, submission.sample, library)
    
            # remember the name of the project and dataset
            submission.vamps_project_name = final_project_code
            submission.vamps_dataset_name = submission.sample
            submission.region = library.region
            # if all went ok then mark this as completed
            submission.next_action = SubmissionORM.ACTION_GAST
            submission.current_status_msg = "Data transfer to VAMPS begun."
            # save it
            self.sess_obj.commit()
        except:
            self.log_to_submission(submission, "Error during preparation and UPLOAD to VAMPS")
        
    # call back to MoBEDAC and get the sequence file....could take a long time
    def download_sequence_file(self, submission, processing_dir):
        try:
            # this will eventually be a URL on mobedac that should get us a stream object?
            mobedac_file_path = get_parm("test_sequence_file_path")
            mobedac_file = open(mobedac_file_path, "r")
            raw_seq_file_name = Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME
            raw_seq_file = open(processing_dir + raw_seq_file_name, 'w')
            buffer_size=8192
            while 1:
                copy_buffer = mobedac_file.read(buffer_size)
                if copy_buffer:
                    raw_seq_file.write(copy_buffer)
                else:
                    break
            raw_seq_file.close()
        except:
            self.log_to_submission(submission, "Error during retrieving of sequence data from MoBEDAC")
            raise
        
    # need to create 4 files to upload to VAMPS
    # sequence file, run key file, primer file and params file
    def create_and_upload(self, submission, sequence_set_name, project_code, project, sample_name, library_obj): 
        processing_dir = self.root_dir + "/" + str(submission.id) + "/"

        # now create the cleaned seq file
        # create the cleaned sequence file also
        clean_sequence_file_name = processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX + "_clean.fa"
        self.convert_raw_to_clean_seq(processing_dir + Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME, Submission_Processor.MOBEDAC_SEQUENCE_FILE_NAME_PREFIX, clean_sequence_file_name)

        # now create the primer file
        # first get the owning Library
        primers = json.loads(library_obj.primers)
        primer_file_name = processing_dir + "primers.txt"
        self.create_primer_file(primers, primer_file_name)
        
        # now create the key file
        run_key = library_obj.run_key
        dataset = sample_name
        key_hash = {"key" : run_key, "direction" : library_obj.direction,
                    "region" : library_obj.region, "project" : project_code, "dataset" : dataset}
        run_key_file_name = processing_dir + "run_key.txt"
        self.write_run_key_file(run_key_file_name, key_hash)
        
        # copy the param file
        submission_opsions_json = json.loads(submission.options)
        param_file_name = processing_dir + "params.prm"
        self.create_params_file(param_file_name, submission_opsions_json['user'], run_key, project.description[0:255], "Dataset description test", project.name)
        
        # now send the files on up
        vamps_status_record_id = self.post_sequence_data(submission, clean_sequence_file_name, primer_file_name, run_key_file_name, param_file_name)
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

        
    def post_sequence_data(self, submission, clean_sequence_file_name, primer_file_name, run_key_file_name, param_file_name):
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
            self.log_debug("Uploaded to VAMPS submission: " + str(submission.id) + " got response id: " + response_str)
            return response_str
        except:
            self.log_exception("Error connecting with VAMPS processor to upload submission: " + str(submission.id))
            raise
        finally:
            pass
    
    def write_run_key_file(self, run_key_file_name, key_hash):
        key_file = open(run_key_file_name, 'w')
        key_line = Template("$key\t$direction\t$region\t$project\t$dataset\n").substitute(key_hash)
        key_file.write(key_line)
        key_file.close()
        
    def convert_raw_to_clean_seq(self, raw_seq_file_name, raw_seq_file_name_prefix, clean_seq_file_name):
        raw_seq_file = open(raw_seq_file_name, 'r')
        clean_seq_file = open(clean_seq_file_name, 'w')
        for seq_record in SeqIO.parse(raw_seq_file, "fasta"):
            parts = seq_record.description.split('|')
            id = parts[0]
            dated_id = id.replace("@@@@@@@@@@", datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
            remainder = "|".join(parts[1:])
            clean_seq_file.write(">%s\t%s\t%s\n" % (dated_id, seq_record.seq, remainder))
            
        raw_seq_file.close()
        clean_seq_file.close()
        
    def create_primer_file(self, primer_array, primer_file_name):
        primer_file = open(primer_file_name, 'w')
        for primer in primer_array:
            primer_line = Template("$name\t$direction\t$sequence\t$regions\t$location\n").substitute(primer)
            primer_file.write(primer_line)
        primer_file.close()
    