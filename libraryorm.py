from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String, DateTime, func
from basemobedac import BaseMoBEDAC
from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from dec_base import Base
from sequencesetorm import SequenceSetORM
import json as json 

#library_sequenceset_table = Table('librarysequenceset', Base.metadata,
#    Column('library_id', Integer, ForeignKey('library.id')),
#    Column('sequenceset_id', Integer, ForeignKey('sequenceset.id')))
class LibraryORM(Base, BaseMoBEDAC):
    __tablename__ = 'library'
    SEQUENCESET_ID_ARRAY = "sequencesets"
    LIB_TYPE = "lib_type"
    LIB_INSERT_LEN = "lib_insert_len"
    SAMPLE_ID = "sample_id"
    RUN_KEY = "run_key"
    PRIMERS = "primers"
    DIRECTION = "direction"
    REGION = "region"
    DOMAIN = "domain"
    
    sample_id = Column(String(64), ForeignKey('sample.id'))
    
    id = Column(String(64), primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    lib_type = Column(String(256))
    lib_insert_len = Column(Integer)
    run_key = Column(String(16))
    primers = Column(MEDIUMTEXT)
    direction = Column(String(16))
    region = Column(String(32))
    domain = Column(String(32))
    sequence_set_ids = Column(String(512))

#    sequencesets = relationship("SequenceSetORM",secondary=library_sequenceset_table)    
    sequencesets = relationship("SequenceSetORM")    
    
    @classmethod
    def get_REST_sub_path(cls):
        return "library"
    
    @classmethod
    def mobedac_name(self):
        return "Library"
    
    @classmethod
    def mobedac_collection_name(self):
        return "libraries"

    def __init__(self, arg_dict):
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<LibraryORM('%s','%s', '%s','%s','%s', '%s')>" % (self.name, self.about, self.url, self.version, self.mbd_metadata, self.creation)
    
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.base_from_json(is_create, json_obj)
        self.set_attrs_from_json(json_obj, self.LIB_TYPE)
        self.set_attrs_from_json(json_obj, self.LIB_INSERT_LEN)

        self.set_attrs_from_json(json_obj, self.RUN_KEY)
        self.primers = json.dumps(json_obj[self.PRIMERS])
        self.set_attrs_from_json(json_obj, self.DIRECTION)
        self.set_attrs_from_json(json_obj, self.REGION)
        self.set_attrs_from_json(json_obj, self.DOMAIN)
        self.set_attrs_from_json(json_obj, self.SAMPLE_ID)
        self.sequence_set_ids = ",".join(json_obj['sequence_set_ids'])
        
        # now put the objects into the real child collection
        # have to do deletes on all existing child sample associations that are not in the new sample set
#        BaseMoBEDAC.update_child_collection(SequenceSetORM, self.sequencesets, json_obj[LibraryORM.SEQUENCESET_IDS], sess_obj)
        return self
    
    def to_json(self, sess_obj):
        base_json = BaseMoBEDAC.to_json(self, sess_obj)
        parts = [base_json]
        # dump derived parts here
        self.dump_attr(parts,self.lib_type, self.LIB_TYPE)
        self.dump_attr(parts,self.lib_insert_len, self.LIB_INSERT_LEN)
        self.dump_attr(parts,self.run_key, self.RUN_KEY)
        self.dump_attr(parts,json.loads(self.primers), self.PRIMERS)
        self.dump_attr(parts,self.direction, self.DIRECTION)
        self.dump_attr(parts,self.region, self.REGION)
        self.dump_attr(parts,self.domain, self.DOMAIN)
        self.dump_attr(parts,self.sample_id, self.SAMPLE_ID)
        #self.dump_attr(parts,self.pi, ProjectORM.PROJECT_PI)
        self.dump_collection_attr(parts, self.sequencesets, self.SEQUENCESET_ID_ARRAY)

        result =  ",".join(parts)
        print result
        return result
   


