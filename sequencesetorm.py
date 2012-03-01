from sqlalchemy import *
import MySQLdb
from sqlalchemy.dialects.mysql import MEDIUMTEXT
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

class SequenceSetORM(Base, BaseMoBEDAC):
    __tablename__ = 'sequenceset'
    
    TYPE = "type"
    PROTEIN = "protein"
    PROVENANCE = "provenance"
    LIBRARY_ID = "library_id"
    SEQUENCES = "sequences"

    id = Column(String(64), primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    type = Column(String(256))
    protein = Column(Boolean)
    provenance = Column(MEDIUMTEXT)
    library_id = Column(String(64), ForeignKey('library.id'))
    sequences = Column(String(512))
    
    @classmethod
    def get_REST_sub_path(cls):
        return "sequenceset"
    
    @classmethod
    def mobedac_name(self):
        return "SequenceSet"
    
    @classmethod
    def mobedac_collection_name(self):
        return "sequencesets"

    def __init__(self, arg_dict):
        pass
    
    def get_one(self):
        pass
    
    def __repr__(self):
        return "<SequenceSetORM('%s','%s', '%s','%s','%s', '%s')>" % (self.name, self.about, self.url, self.version, self.mbd_metadata, self.creation)
    
    def from_json(self, is_create, json_obj, sess_obj):
        # do base attrs
        self.base_from_json(is_create, json_obj)
        self.set_attrs_from_json(json_obj, self.TYPE)
        self.protein = json_obj[self.PROTEIN]
        self.set_attrs_from_json(json_obj, self.PROTEIN)
        self.set_attrs_from_json(json_obj, self.PROVENANCE)
        self.set_attrs_from_json(json_obj, self.SEQUENCES)
        self.set_attrs_from_json(json_obj, self.LIBRARY_ID)
        return self
    
    def to_json(self, sess_obj):
        base_json = BaseMoBEDAC.to_json(self, sess_obj)
        parts = [base_json]

        self.dump_attr(parts,self.type, self.TYPE)
        self.dump_attr(parts,self.protein, self.PROTEIN)
        self.dump_attr(parts,self.provenance, self.PROVENANCE)
        self.dump_attr(parts,self.provenance, self.SEQUENCES)
        self.dump_attr(parts,self.library_id, self.LIBRARY_ID)
        result =  ",".join(parts)
        print result
        return result
    
