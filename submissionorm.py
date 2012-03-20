from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT, BIGINT
from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from basemobedac import BaseMoBEDAC
from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from dec_base import Base
import json as json
from Bio import SeqIO
import os
import datetime
from string import Template
from projectorm import ProjectORM
from sampleorm import SampleORM
from libraryorm import LibraryORM
from ftplib import FTP
from rest_log import mobedac_logger
from dbconn import vampsSession, test_engine
from submission_detailsorm import SubmissionDetailsORM
from submission_exception import SubmissionException


class SubmissionORM(Base, BaseMoBEDAC):
    __tablename__ = 'submission'

    ID = 'id'
    ANALYSIS_PARAMS = 'analysis_params'
    LIBRARY_IDS = 'library_ids'
    USER = 'user'
    AUTH_KEY = 'auth'
    
    id = Column(Integer, primary_key=True)
    analysis_params_str = Column(String(1024))
    library_ids_str = Column(String(1024))
    user = Column(String(32))
    auth_key = Column(String(128))
    
    @classmethod
    def mobedac_name(self):
        return "Submission"
    
    @classmethod
    def mobedac_collection_name(self):
        return "submissions"

    def __init__(self, arg_dict):
        self.sess_obj = None
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<SubmissionORM('%s'')>" % (self.id)
    
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.library_ids = json_obj[self.LIBRARY_IDS]
        self.library_ids_str = json.dumps(self.library_ids)
        self.analysis_params_str = json.dumps(json_obj[self.ANALYSIS_PARAMS]) 
        self.analysis_params = json_obj[self.ANALYSIS_PARAMS] 
        self.user = self.analysis_params[self.USER]
        self.auth_key = self.analysis_params[self.AUTH_KEY]
        return self
    
    def to_json(self, sess_obj):
        parts = []
        
        self.dump_attr(parts,self.user, SubmissionORM.USER)
        self.dump_attr(parts,self.id, SubmissionORM.ID)
        
        params_as_dictionary = json.loads(self.analysis_params_str)
        self.dump_attr(parts,params_as_dictionary, SubmissionORM.ANALYSIS_PARAMS)
        library_ids_as_array = json.loads(self.library_ids_str)
        self.dump_attr(parts,library_ids_as_array, SubmissionORM.LIBRARY_IDS)
        # status block...need overall status and per library status
        # get all detail objects
        status_hash = {}
        # assume an overall success unless there is somekind of error or incomplete in one of the details objects
        overall_status = SubmissionDetailsORM.COMPLETE_SUCCESS_STATUS
        overall_status_msg = "Processing complete"
        for detail in sess_obj.query(SubmissionDetailsORM).filter(SubmissionDetailsORM.submission_id == self.id).all():
            status_hash[detail.library_id] = detail.get_current_status()    
            # any in process or error?
            if status_hash[detail.library_id]['status_code'] == SubmissionDetailsORM.ERROR_STATUS:
                overall_status = SubmissionDetailsORM.ERROR_STATUS
                overall_status_msg = "There was a processing error."
            # any still in process...if so mark the overall as in process unless
            # the overall is already marked as ERROR then don't overwrite that!
            if overall_status != SubmissionDetailsORM.ERROR_STATUS and status_hash[detail.library_id]['status_code'] == SubmissionDetailsORM.PROCESSING_STATUS:
                overall_status = SubmissionDetailsORM.PROCESSING_STATUS
                overall_status_msg = "VAMPS is still processing the data."
        self.dump_attr(parts, overall_status, "status_code")
        self.dump_attr(parts, overall_status_msg, "current_status")
        self.dump_attr(parts, status_hash, "library_statuses")
        # we will eventually want to query the VAMPS db to get the status
        result =  ",".join(parts)
        return result

    

    def initialize_for_processing(self, sess_obj):
        
        # need to call back to mobedac and figure out all the other objects etc
        libraries = self.library_ids
        # now loop and gather all info
        project_hash = {}
        sample_hash = {}
        library_hash = {}
        detail_objs = []
        for lib_id in libraries:
            try:
                mobedac_logger.info("Retrieving remote library: " + lib_id);
                library_hash[lib_id] = curr_library = LibraryORM.get_remote_instance(lib_id, None, sess_obj)
            except Exception as e:
                # some kind of error 
                raise SubmissionException("There was an error retrieving library: " + lib_id + " error: " + e.value)
                
            sample_id = curr_library.sample
            try:
                mobedac_logger.info("Retrieving remote sample: " + sample_id);
                sample_hash[sample_id] = curr_sample = SampleORM.get_remote_instance(sample_id, None, sess_obj)
            except Exception as e:
                # some kind of error 
                raise SubmissionException("There was an error retrieving sample: " + sample_id + " error: " + e.value)
            
            project_id = curr_sample.project
            try:
                mobedac_logger.info("Retrieving remote project: " + project_id);
                project_hash[project_id] = curr_project = ProjectORM.get_remote_instance(project_id, None, sess_obj)
                mobedac_logger.info("done Retrieving remote project: " + project_id);
            except Exception as e:
                # some kind of error 
                raise SubmissionException("There was an error retrieving project: " + project_id + " error: " + e.value)

            # do some sanity check/validation on the library and project information
            mobedac_logger.info("library domain: " + curr_library.get_domain())
            mobedac_logger.info("library run_key: " + curr_library.get_run_key())
            mobedac_logger.info("library region: " + curr_library.get_region())
            mobedac_logger.info("project metadatastr: " + curr_project.mbd_metadata)
            if not(curr_library.get_run_key()):
                raise SubmissionException("The library: " + lib_id + " is missing a run key")
            if not(curr_library.get_domain()):
                raise SubmissionException("The library: " + lib_id + " is missing a domain")
            if not(curr_library.get_region()):
                raise SubmissionException("The library: " + lib_id + " is missing a region")
            #if not(curr_project.get_metadata_json()['project_code']):
                raise SubmissionException("The project: " + lib_id + " is missing a project_code")
            #check the primers
            primers = curr_library.get_primers()
            # if only 1 primer and it isn't a BOTH direction then complain
            forward_found = False
            reverse_found = False
            mobedac_logger.info("done Retrieving remote objects");
            for primer in primers:
                dir = primer['direction'].lower()
                if dir == 'f':
                    forward_found = True
                elif dir == 'r':
                    reverse_found = True
            if not(forward_found) or not(reverse_found):
                raise SubmissionException("You must supply at least 1 forward primer and 1 reverse primer.")
            mobedac_logger.info("done with primers");
            
            # now what will the official project name be in vamps for this library?
            curr_library_domain = curr_library.get_domain()
            curr_library_region = curr_library.get_region()
            domain_region_suffix = '_' + curr_library_domain[0].upper() + curr_library_region.lower()
            vamps_project_name = curr_project.get_metadata_json()['project_code'] + domain_region_suffix
            mobedac_logger.info("preparing the submission detail object");
            # now create the submission details objects
            new_details = SubmissionDetailsORM(None)
            new_details.project_id = project_id
            new_details.library_id = lib_id
            new_details.sample_id = sample_id
            new_details.region = curr_library_region.lower()
            new_details.vamps_project_name = vamps_project_name
            detail_objs.append(new_details)
            # mobedac uses periods...we don't want them
            dataset_name = curr_library.id.replace('.', '_')
            new_details.vamps_dataset_name = dataset_name
            new_details.sequenceset_id = curr_library.get_sequence_set_id_array()[0] # just take the first one for now
            mobedac_logger.info("new_details has sequence set id: " + new_details.sequenceset_id)
            new_details.next_action = SubmissionDetailsORM.ACTION_DOWNLOAD
            mobedac_logger.info("DONE preparing the submission detail object");

        try:
            # make sure to write this submission out before anything
            sess_obj.add(self)
            mobedac_logger.info("committing all submission detail objects");
            sess_obj.commit()
            # now set the submission id into each of these submission_detail objects since everything worked out ok
            # because only now do we have a submission id (self)
            for new_detail in detail_objs:
                new_detail.submission_id = self.id
                sess_obj.add(new_detail)
            sess_obj.commit()
            mobedac_logger.info("committing submission object");
        except Exception as e:
            raise SubmissionException("There was an error during submission: " + e.value)
