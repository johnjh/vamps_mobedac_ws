from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String, DateTime, func
from basemobedac import BaseMoBEDAC
from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from dec_base import Base
from sampleorm import SampleORM

#project_sample_table = Table('projectsample', Base.metadata,
#    Column('project_id', Integer, ForeignKey('project.id')),
#    Column('sample_id', Integer, ForeignKey('sample.id')))
class ProjectORM(Base, BaseMoBEDAC):
    __tablename__ = 'project'
    PROJECT_TITLE = 'title'
    PROJECT_PI = 'pi'
    PROJECT_DESCRIPTION = 'description'
    PROJECT_FUNDING_SOURCE = 'funding_source'
    PROJECT_SAMPLES = 'samples'
    PROJECT_SEQUENCE_SET_IDS = 'sequence_set_ids'

    id = Column(String(64), primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    #samples = relationship("SampleORM")    
    
    # mine
    pi = Column(String(256))
    funding_source = Column(String(1024))
    description = Column(String(1024)) 

    @classmethod
    def get_REST_sub_path(cls):
        return "project"

    
    @classmethod
    def mobedac_name(self):
        return "Project"
    
    @classmethod
    def mobedac_collection_name(self):
        return "projects"

    def __init__(self, arg_dict):
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<ProjectORM('%s','%s', '%s','%s','%s', '%s', '%s')>" % (self.name, self.about, self.url, self.version, self.mbd_metadata, self.creation, self.pi)
    
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.base_from_json(is_create, json_obj)
        # now our attrs
        self.set_attrs_from_json(json_obj, ProjectORM.PROJECT_PI)
        self.set_attrs_from_json(json_obj, ProjectORM.PROJECT_FUNDING_SOURCE)
        self.set_attrs_from_json(json_obj, ProjectORM.PROJECT_DESCRIPTION)
        # now put the objects into the real child collection
        # have to do deletes on all existing child sample associations that are not in the new sample set
#        BaseMoBEDAC.update_child_collection(SampleORM, self.samples, json_obj[ProjectORM.PROJECT_SAMPLES], sess_obj)
        return self
    
    def to_json(self, sess_obj):
        base_json = BaseMoBEDAC.to_json(self, sess_obj)
        parts = [base_json]
        self.dump_attr(parts,self.pi, ProjectORM.PROJECT_PI)
        self.dump_attr(parts,self.funding_source, ProjectORM.PROJECT_FUNDING_SOURCE)
        self.dump_attr(parts,self.description, ProjectORM.PROJECT_DESCRIPTION)
        #self.dump_collection_attr(parts, self.samples, 'samples')
        result =  ",".join(parts)
        print result
        return result
   


