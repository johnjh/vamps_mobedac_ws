from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String, DateTime, func
from basemobedac import BaseMoBEDAC
from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from dec_base import Base
from libraryorm import LibraryORM
from rest_log import mobedac_logger
from dbconn import vampsSession, test_engine


class SubmissionDetailsORM(Base, BaseMoBEDAC):
    __tablename__ = 'submission_details'
    
    PROCESSING_STATUS = 0
    COMPLETE_SUCCESS_STATUS = 1
    COMPLETE_WARNING_STATUS = 2
    ERROR_STATUS = 3
    
    ACTION_DOWNLOAD = "download"
    ACTION_VAMPS_UPLOAD = "vamps_upload"
    ACTION_GAST = "gast"
    ACTION_POST_RESULTS_TO_MOBEDAC = "post_results_to_mobedac"
    ACTION_PROCESSING_COMPLETE = "processing_complete"
    
    
    ID = "id"
    PROJECT_ID = "project_id"
    SUBMISSION_ID = "submission_id"
    SAMPLE_ID = "sample_id"
    LIBRARY_ID = "library_id"
    SEQUENCESET_ID = "sequenceset_id"
    VAMPS_PROJECT_NAME = "vamps_project_name"
    VAMPS_DATASET_NAME = "vamps_dataset_name"
    VAMPS_STATUS_RECORD_ID = "vamps_status_record_id"
    NEXT_ACTION = "next_action"
    REGION = 'region'
    CURRENT_STATUS_MSG = "current_status_msg"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String(64))    
    submission_id = Column(String(64), ForeignKey('submission.id'))    
    sample_id = Column(String(64))    
    library_id = Column(String(64))    
    sequenceset_id = Column(String(64))    
    vamps_project_name = Column(String(64))    
    vamps_dataset_name = Column(String(64))    
    next_action = Column(String(64))    
    vamps_status_record_id = Column(Integer)
    region = Column(String(32))
    current_status_msg = Column(String(512))

    @classmethod
    def get_REST_sub_path(cls):
        return "submission_details"
    
    
    @classmethod
    def mobedac_name(self):
        return "SubmissionDetails"
    
    @classmethod
    def mobedac_collection_name(self):
        return "submission_details"

    def __init__(self, arg_dict):
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<SubmissionDetailsORM('%s','%s', '%s','%s','%s', '%s')>" % (self.id, self.submission_id, self.project_id, self.sample_id, self.library_id, self.sequenceset_id)
    
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
    
    def get_current_status(self):
        status = {}
        try:
            # this is more complicated since there is no message on our side so at this point
            # this web service does not think there is an error...but perhaps VAMPS has run
            # into an error?
            if self.next_action == self.ACTION_DOWNLOAD:
                # we are telling them that VAMPS is doing the retrieval but it is really
                # this web service that grabs the data and then passes it off to VAMPS
                msg = "The VAMPS system is still retrieving the data from MoBEDAC."
                code = self.PROCESSING_STATUS
            elif self.next_action == self.ACTION_VAMPS_UPLOAD:
                msg = "The data has been retrieved from MoBEDAC and will soon be uploaded to the VAMPS processor."
                code = self.PROCESSING_STATUS
            elif self.next_action == self.ACTION_GAST:
                # so at this point this WS successfully passed the data off to VAMPS who
                # is doing the trimming...we need to check with VAMPS 
                vamps_status_row = self.get_VAMPS_submission_status_row(None)     
                # need to get the status value
                status = vamps_status_row[0]
                if status == 'TRIM_ERROR':
                    # for now
                    msg = "There was an error during VAMPS upload processing"
                    code = self.ERROR_STATUS
                elif status == 'TRIM_PROCESSING':
                    # for now
                    msg = "The data is being uploaded and quality checked by the VAMPS system."
                    code = self.PROCESSING_STATUS
                else:
                    # for now
                    msg = "The data was successfully uploaded and quality checked by VAMPS and is awaiting GAST processing"
                    code = self.PROCESSING_STATUS
            elif self.next_action == self.ACTION_POST_RESULTS_TO_MOBEDAC:
                # at this point the WS started up the GAST on VAMPS and so we need to check
                # with VAMPS to check the VAMPS Gasting status
                vamps_status_row = self.get_VAMPS_submission_status_row(None)  
                status = vamps_status_row[0]
                if status == 'GAST_PROCESSING':
                    msg = "The VAMPS system is performing GAST processing."   
                    code = self.PROCESSING_STATUS
                elif status == 'GAST_SUCCESS':
                    msg = "The VAMPS system has successfully completed the GAST processing. And needs to be returned to MoBEDAC"   
                    code = self.PROCESSING_STATUS
                elif status == 'GAST_ERROR':
                    msg = "There was an error during GAST processing"
                    code = self.ERROR_STATUS
            elif self.next_action == self.ACTION_PROCESSING_COMPLETE:
                msg = "Processing is complete and data has been returned to MoBEDAC."
                code = self.COMPLETE_SUCCESS_STATUS
            else:
                # this is kind of an error state?
                msg = "The submission is in state: " + self.next_action
                code = 4
        except:
            mobedac_logger.exception("submissionORM error generating submission status message")
            msg = "There was an error retrieving the status of this submission"
            code = self.ERROR_STATUS
        return {"status_code" : code, "current_status" : msg}
        
        
        
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.PROJECT_ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.SUBMISSION_ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.SAMPLE_ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.LIBRARY_ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.SEQUENCESET_ID)
        self.set_attrs_from_json(json_obj, SubmissionDetailsORM.VAMPS_PROJECT_NAME)        
        return self
    
    def to_json(self, sess_obj):
        parts = []
        # dump derived parts here
        self.dump_attr(parts,self.id, self.ID)
        self.dump_attr(parts,self.project_id, self.PROJECT_ID)
        self.dump_attr(parts,self.submission_id, self.SUBMISSION_ID)
        self.dump_attr(parts,self.sample_id, self.SAMPLE_ID)
        self.dump_attr(parts,self.library_id, self.LIBRARY_ID)
        self.dump_attr(parts,self.sequenceset_id, self.SEQUENCESET_ID)
        self.dump_attr(parts,self.vamps_project_name, self.VAMPS_PROJECT_NAME)
        self.dump_attr(parts,self.vamps_dataset_name, self.VAMPS_DATASET_NAME)
        self.dump_attr(parts,self.next_action, self.NEXT_ACTION)
        self.dump_attr(parts,self.vamps_status_record_id, self.VAMPS_STATUS_RECORD_ID)
        # get status
        status_hash = self.get_current_status()
        self.dump_attr(parts, status_hash['status_code'], "status_code")
        self.dump_attr(parts,status_hash['current_status'], "current_status")
        
        
        result =  ",".join(parts)
        return result
   


