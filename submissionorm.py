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
from dbconn import vampsSession


class SubmissionORM(Base, BaseMoBEDAC):
    __tablename__ = 'submission'

    ACTION_DOWNLOAD = "download"
    ACTION_VAMPS_UPLOAD = "vamps_upload"
    ACTION_GAST = "gast"
    ACTION_GAST_COMPLETE = "gast_complete"
    VAMPS_PROJECT_NAME = "vamps_project_name"
    VAMPS_DATASET_NAME = "vamps_dataset_name"
    PROJECT = "project"
    SAMPLE = "sample"
    LIBRARY = "library"
    SEQUENCE_SET = "sequence_set"
    OPTIONS = "options"
    
    # valid values download, vamps_upload, gast
    NEXT_ACTION = "next_action"
    
    VAMPS_STATUS_RECORD_ID = "vamps_status_record_id"
    CURRENT_STATUS_MSG = "current_status_msg"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    
    # these don't have the _ID because they are ID's of objects on the MoBEDAC server not on the VAMPS box
    library = Column(String(32))
    project = Column(String(32))
    sample = Column(String(32))
    sequence_set = Column(String(32))
    vamps_status_record_id = Column(String(32))
    
    options = Column(String(1024))
    current_status_msg = Column(String(1024))
    next_action = Column(String(45))
    vamps_project_name = Column(String(128))
    vamps_dataset_name = Column(String(128))
    region = Column(String(45))
    
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
        return "<SubmissionORM('%s','%s', '%s','%s','%s', '%s')>" % (self.name, self.about, self.url, self.version, self.mbd_metadata, self.creation)
    
    def get_VAMPS_submission_status_row(self, sess_obj):
        vamps_session = None
        try:
            vamps_session = vampsSession()
            result_row = vamps_session.execute("SELECT status, status_message FROM vamps_upload_status where id=:id", {'id':self.vamps_status_record_id}).first()      
            return result_row
        except:
            mobedac_logger.exception("submissionORM error retrieving vamps_upload_status with id: " + self.vamps_status_record_id)
            raise
        finally:
            vamps_session.close()

        
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.base_from_json(is_create, json_obj)
        self.set_attrs_from_json(json_obj, SubmissionORM.PROJECT)
        self.set_attrs_from_json(json_obj, SubmissionORM.SAMPLE)
        self.set_attrs_from_json(json_obj, SubmissionORM.LIBRARY)
        self.set_attrs_from_json(json_obj, SubmissionORM.SEQUENCE_SET)
        self.options = json.dumps(json_obj[self.OPTIONS])
        self.vamps_submitted = False
        return self

    def post_create(self, sess_obj):
        self.next_action = self.ACTION_DOWNLOAD
        sess_obj.add(self)
        sess_obj.commit()
    
    def to_json(self):
        base_json = BaseMoBEDAC.to_json(self)
        parts = [base_json]
        self.dump_attr(parts,self.project, SubmissionORM.PROJECT)
        self.dump_attr(parts,self.sample, SubmissionORM.SAMPLE)
        self.dump_attr(parts,self.library, SubmissionORM.LIBRARY)
        self.dump_attr(parts,self.sequence_set, SubmissionORM.SEQUENCE_SET)
        self.dump_attr(parts,json.loads(self.options), SubmissionORM.OPTIONS)
        self.dump_attr(parts,self.vamps_project_name, SubmissionORM.VAMPS_PROJECT_NAME)
        self.dump_attr(parts,self.vamps_dataset_name, SubmissionORM.VAMPS_DATASET_NAME)
        # how to give back the status msg...we only keep text when there is an error
        if self.current_status_msg != None:
            self.dump_attr(parts,self.current_status_msg, SubmissionORM.CURRENT_STATUS_MSG)
        else:
            try:
                # this is more complicated since there is no message on our side so at this point
                # this web service does not think there is an error...but perhaps VAMPS has run
                # into an error?
                if self.next_action == self.ACTION_DOWNLOAD:
                    # we are telling them that VAMPS is doing the retrieval but it is really
                    # this web service that grabs the data and then passes it off to VAMPS
                    msg = "The VAMPS system is still retrieving the data from MoBEDAC."
                elif self.next_action == self.ACTION_VAMPS_UPLOAD:
                    msg = "The data has been retrieved from MoBEDAC and will soon be uploaded to the VAMPS processor."
                elif self.next_action == self.ACTION_GAST:
                    # so at this point this WS successfully passed the data off to VAMPS who
                    # is doing the trimming...we need to check with VAMPS 
                    vamps_status_row = self.get_VAMPS_submission_status_row(None)     
                    # need to get the status value
                    # for now
                    msg = "The data is being uploaded and quality checked by the VAMPS system."
                elif self.next_action == self.ACTION_GAST_COMPLETE:
                    # at this point the WS started up the GAST on VAMPS and so we need to check
                    # with VAMPS to check the VAMPS Gasting status
                    vamps_status_row = self.get_VAMPS_submission_status_row(None)     
                    msg = "The VAMPS system is performing a GAST on the sequence data."
                else:
                    # this is kind of an error state?
                    msg = "The submission is stopped"
            except:
                mobedac_logger.exception("submissionORM error generating submission status message")
                msg = "There was an error retrieving the status of this submission"
            self.dump_attr(parts,msg, SubmissionORM.CURRENT_STATUS_MSG)
        
        # we will eventually want to query the VAMPS db to get the status
        result =  ",".join(parts)
        print result
        return result

