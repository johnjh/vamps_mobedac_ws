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
    LIBRARY_ID = "library"
    DOMAIN = "domain"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    about = Column(String(1024))
    url = Column(String(512))
    version = Column(Integer)  
    mbd_metadata = Column('metadata',MEDIUMTEXT)
    creation = Column(DateTime)
    type = Column(String(256))
    domain = Column(String(32))
    protein = Column(Boolean)
    provenance = Column(MEDIUMTEXT)
    library_id = Column(Integer, ForeignKey('library.id'))
    
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
#        self.protein = True if (json_obj[self.PROTEIN].lowercase()=='true') else False
        self.set_attrs_from_json(json_obj, self.PROTEIN)
        self.set_attrs_from_json(json_obj, self.PROVENANCE)
        self.set_attrs_from_json(json_obj, self.DOMAIN)
        self.library_id = int(json_obj["library"])
        return self
    
    def to_json(self):
        base_json = BaseMoBEDAC.to_json(self)
        parts = [base_json]

        self.dump_attr(parts,self.type, self.TYPE)
        self.dump_attr(parts,self.protein, self.PROTEIN)
        self.dump_attr(parts,self.provenance, self.PROVENANCE)
        self.dump_attr(parts,self.domain, self.DOMAIN)
        self.dump_attr(parts,self.library_id, self.LIBRARY_ID)
        result =  ",".join(parts)
        print result
        return result
    
    @classmethod
    def create_and_upload(self, params, new_sequenceset_obj, library_obj, sess_obj): 
        # get assigne the object attributes from json data in the json file that was uploaded
        sess_obj.add(new_sequenceset_obj)
        # lots of file creation ahead!
        # lets create a directory to store it
        root_dir = "/Users/johnhufnagle/Documents/workspace/mobedac_rest"
        upload_dir = root_dir + "/" + datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
        os.mkdir(upload_dir)
        # need some validation here
        # can't create a sequence set tied to a library where the libraries owning Sample is not currently
        # attached to a Project
        # how to code that up?
        # upload the file and create the object too
        uploaded_file_obj = params['upload'].file
        raw_seq_file_name_prefix = new_sequenceset_obj.name + "_raw_seq"
        raw_seq_file_name = raw_seq_file_name_prefix + ".fa"
        # read from upload and write the raw file
        new_sequenceset_obj.write_raw_seq_file(upload_dir + "/" + raw_seq_file_name, uploaded_file_obj)
        # now create the cleaned seq file
        # create the cleaned sequence file also
        new_sequenceset_obj.convert_raw_to_clean_seq(upload_dir + "/" + raw_seq_file_name, raw_seq_file_name_prefix, upload_dir + "/" + raw_seq_file_name_prefix + "_clean.fa")

        # now create the primer file
        # first get the owning Library
        primers = json.loads(library_obj.primers)
        new_sequenceset_obj.create_primer_file(primers, upload_dir + "/" + "primers.txt")
        
        # now create the key file
        run_key = library_obj.run_key
        project = "testprj"
        dataset = "ds1"
        key_hash = {"key" : run_key, "direction" : library_obj.direction,
                    "region" : library_obj.region, "project" : project, "dataset" : dataset}
        new_sequenceset_obj.write_run_key_file(upload_dir + "/" + "run_key.txt", key_hash)
        
        return new_sequenceset_obj
    
    def write_run_key_file(self, run_key_file_name, key_hash):
        key_file = open(run_key_file_name, 'w')
        key_line = Template("$key\t$direction\t$region\t$project\t$dataset\n").substitute(key_hash)
        key_file.write(key_line)
        key_file.close()

    def write_raw_seq_file(self, raw_seq_file_name, source_file_obj):
        raw_seq_file = open(raw_seq_file_name, 'w')
        buffer_size=8192
        while 1:
            copy_buffer = source_file_obj.read(buffer_size)
            if copy_buffer:
                raw_seq_file.write(copy_buffer)
            else:
                break
        raw_seq_file.close()
        
    def convert_raw_to_clean_seq(self, raw_seq_file_name, raw_seq_file_name_prefix, clean_seq_file_name):
        raw_seq_file = open(raw_seq_file_name, 'r')
        clean_seq_file = open(clean_seq_file_name, 'w')
        for seq_record in SeqIO.parse(raw_seq_file, "fasta"):
            parts = seq_record.description.split('|')
            id = parts[0]
            remainder = "|".join(parts[1:])
            clean_seq_file.write("%s\t%s\t%s\n" % (id, seq_record.seq, remainder))
        raw_seq_file.close()
        clean_seq_file.close()
        
    def create_primer_file(self, primer_array, primer_file_name):
        primer_file = open(primer_file_name, 'w')
        for primer in primer_array:
            primer_line = Template("$name\t$direction\t$sequence\t$regions\t$location\n").substitute(primer)
            primer_file.write(primer_line)
        primer_file.close()
        
        

