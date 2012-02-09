from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String, DateTime, func
from basemobedac import BaseMoBEDAC
from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from dec_base import Base
from libraryorm import LibraryORM

class SampleORM(Base, BaseMoBEDAC):
    __tablename__ = 'sample'
    PROJECT_ID = "project_id"
    LIBRARY_IDS = "libraries"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    project_id = Column(String(64), ForeignKey('project.id'))    

#    libraries = relationship("LibraryORM",secondary=sample_library_table)    
    libraries = relationship("LibraryORM")    

    @classmethod
    def get_REST_sub_path(cls):
        return "sample"
    
    
    @classmethod
    def mobedac_name(self):
        return "Sample"
    
    @classmethod
    def mobedac_collection_name(self):
        return "samples"

    def __init__(self, arg_dict):
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<SampleORM('%s','%s', '%s','%s','%s', '%s')>" % (self.name, self.about, self.url, self.version, self.mbd_metadata, self.creation)
    
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.base_from_json(is_create, json_obj)
        self.set_attrs_from_json(json_obj, SampleORM.PROJECT_ID)
        return self
    
    def to_json(self, sess_obj):
        base_json = BaseMoBEDAC.to_json(self, sess_obj)
        parts = [base_json]
        # dump derived parts here
        self.dump_attr(parts,self.project_id, self.PROJECT_ID)
        
        self.dump_collection_attr(parts, self.libraries, 'libraries')
        
        result =  ",".join(parts)
        print result
        return result
   


