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
from rest_log import mobedac_logger

#library_sequenceset_table = Table('librarysequenceset', Base.metadata,
#    Column('library_id', Integer, ForeignKey('library.id')),
#    Column('sequenceset_id', Integer, ForeignKey('sequenceset.id')))
class LibraryORM(Base, BaseMoBEDAC):
    __tablename__ = 'library'
    SEQUENCESET_ID_ARRAY = "sequence_sets"
    LIB_TYPE = "lib_type"
    LIB_INSERT_LEN = "lib_insert_len"
    SAMPLE = "sample"
    RUN_KEY = "run_key"
    PRIMERS = "primers"
    DIRECTION = "direction"
    REGION = "region"
    DOMAIN = "domain"
    
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
    sample = ""
    
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

        self.set_attrs_from_json(json_obj, self.SAMPLE)
        self.sequence_set_ids = ",".join(json_obj[self.SEQUENCESET_ID_ARRAY])  # just keep this as a string everywhere until being used
        mobedac_logger.info("library has sequence set ids: " + self.sequence_set_ids)
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
        self.dump_attr(parts,self.sample, self.SAMPLE)
        self.dump_attr(parts,json.loads(self.sequence_set_ids), self.SEQUENCESET_ID_ARRAY)

        result =  ",".join(parts)
        print result
        return result
    
    def get_sequence_set_id_array(self):
        return json.loads(self.sequence_set_ids)
   
    def get_run_key(self):
        lib_metadata = json.loads(self.mbd_metadata)
        return lib_metadata['run_key']
        
    def get_direction(self):
        lib_metadata = json.loads(self.mbd_metadata)
        return lib_metadata['direction']
        
    def get_domain(self):
        lib_metadata = json.loads(self.mbd_metadata)
        return lib_metadata['domain']
        
    def get_region(self):
        lib_metadata = json.loads(self.mbd_metadata)
        return lib_metadata['region']
                
    def get_primers(self):
        lib_metadata = json.loads(self.mbd_metadata)
        primer_count = int(lib_metadata['num_primers'])
        primers = []
        for i in range(1,primer_count+1):
            primer = {}
            primer['name'] = lib_metadata['primer_' + str(i) + '_name']
            primer['direction'] = lib_metadata['primer_' + str(i) + '_direction']
            primer['sequence'] = lib_metadata['primer_' + str(i) + '_sequence']
            primer['regions'] = lib_metadata['primer_' + str(i) + '_region']
            primer['location'] = lib_metadata['primer_' + str(i) + '_location']
            primers.append(primer)
        return primers


