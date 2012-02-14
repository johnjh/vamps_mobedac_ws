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


class SubmissionORM(Base, BaseMoBEDAC):
    __tablename__ = 'submission'

    ID = 'id'
    ANALYSIS_PARAMS = 'analysis_params'
    LIBRARY_IDS = 'library_ids'
    USER = 'user'
    
    id = Column(Integer, primary_key=True)
    analysis_params_str = Column(String(1024))
    library_ids_str = Column(String(1024))
    user = Column(String(32))
    
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
        # make sure to write this submission out before anything
        sess_obj.add(self)
        sess_obj.commit()

        # need to call back to mobedac and figure out all the other objects etc
        libraries = self.library_ids
        # now loop and gather all info
        project_hash = {}
        sample_hash = {}
        library_hash = {}
        sequence_set_hash = {}
        for lib_id in libraries:
            library_hash[lib_id] = curr_library = LibraryORM.get_remote_instance(lib_id, None, sess_obj)
            sample_id = curr_library.sample_id
            sample_hash[sample_id] = curr_sample = SampleORM.get_remote_instance(sample_id, None, sess_obj)
            project_id = curr_sample.project_id
            project_hash[project_id] = curr_project = ProjectORM.get_remote_instance(project_id, None, sess_obj)
            # now what will the official project name be in vamps for this library?
            curr_library_domain = curr_library.domain
            curr_library_region = curr_library.region
            domain_region_suffix = '_' + curr_library_domain[0].upper() + curr_library_region.lower()
            vamps_project_name = curr_project.get_metadata_json()['project_code'] + domain_region_suffix
            # now create the submission details objects
            new_details = SubmissionDetailsORM(None)
            new_details.submission_id = self.id
            new_details.project_id = project_id
            new_details.library_id = lib_id
            new_details.sample_id = sample_id
            new_details.region = curr_library_region.lower()
            new_details.vamps_project_name = vamps_project_name
            # mobedac uses periods...we don't want them
            dataset_name = curr_library.id.replace('.', '_')
            new_details.vamps_dataset_name = dataset_name
            new_details.sequenceset_id = curr_library.sequence_set_ids.split(", ")[0]
            mbd_json = json.loads(curr_sample.mbd_metadata)
            new_details.next_action = SubmissionDetailsORM.ACTION_DOWNLOAD
            sess_obj.add(new_details)
            
        # now set the status                
        self.next_action = 'HALT'
        sess_obj.commit()
    
