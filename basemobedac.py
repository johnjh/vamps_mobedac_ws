import sys, traceback
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
import json as json 
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String
import httplib, urllib
from unidecode import unidecode


class BaseMoBEDAC():
    BASE_ID = "id"
    BASE_NAME = "name"
    BASE_ABOUT = "about"
    BASE_URL = "url"
    BASE_VERSION = "version"
    BASE_METADATA = "metadata"
    BASE_CREATION = "creation"
    
    @classmethod
    def get_remote_instance(cls, id, source, sess_obj):
        conn = None
        try:
            if False:
                headers = {'content-type': 'application/json'}
                conn = httplib.HTTPConnection("api.metagenomics.anl.gov")
                object_path = cls.get_REST_sub_path()
                conn.request("GET", "/" + object_path + "/" + id)
                response = conn.getresponse()
                data = response.read()
                # if all went ok then build an object
                if response.status != httplib.OK:
                    return None
                new_obj = cls({})
                decoded_data = unidecode(data)
                json_obj = json.loads(decoded_data)
                new_obj.from_json(True, json_obj, sess_obj)
            new_obj = cls.get_instance(id, sess_obj)
            return new_obj
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)   
            raise         
        finally:
            if conn != None:
                conn.close() 
            
    
    @classmethod
    def query(self, vpath):
        pass
        
    @classmethod
    def get_all(self,sess):
        try:
            objs = {}
            for row in sess.query(self).order_by(self.id).all():
                objs[str(row.id)] = row.to_json()
            return objs
        except NoResultFound:
            # this is ok
            return None

    @classmethod
    def get_instance(self,idval,sess):
        try:
            obj = sess.query(self).filter(self.id == idval).one()
            return obj 
        except NoResultFound:
            # this is ok
            return None
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            
                        
    def set_attrs_from_json(self, json_obj, key):
        """assign an instance variable of the same name as json value key using
        will have to eventually deal with json keys that are not the same as my data members
         """
        try:
            setattr(self, key, json_obj[key])
        except:
            setattr(self, key, None)

    def base_from_json(self, is_create, json_obj):
        self.set_attrs_from_json(json_obj, self.BASE_ID)
        self.set_attrs_from_json(json_obj, self.BASE_NAME)
        self.set_attrs_from_json(json_obj, self.BASE_ABOUT)
        self.set_attrs_from_json(json_obj, self.BASE_URL)
        self.mbd_metadata = json.dumps(json_obj[self.BASE_METADATA])
        # is this an update?
        if is_create:    
            self.creation = func.now()
        self.version = (1) if is_create else self.version + 1
    
    @classmethod
    def dump_attr(self, parts, val, key):
        if val == None:
            return ""
        parts.append('\n"%s" : %s' % (key, json.dumps(val, sort_keys=False, indent=4)))     
        return parts       
    
    @classmethod
    def dump_collection_attr(self, parts, coll, key):
        child_ids = []
        for child in coll:
            child_ids.append(str(child.id))
        self.dump_attr(parts,child_ids, key)
        
    @classmethod
    def update_child_collection(self, child_class, child_collection, new_child_ids, sess_obj):
        existing_child_ids = []
        for existing_child in child_collection:
            existing_child_ids.append(existing_child.id) # keep a list of existing ids only
            if existing_child.id not in new_child_ids:
                child_collection.remove(existing_child)
        # now add the new ones
        for new_child_id in new_child_ids:
            if new_child_id not in existing_child_ids:
                # find it
                # hey!!! this id might not exist...do we bomb out or just ignore it?
                new_child = child_class.get_instance(new_child_id, sess_obj)
                if new_child != None:
                    child_collection.append(new_child)
    
    def to_json(self, sess_obj):
        parts = []
        self.dump_attr(parts,str(self.id), self.BASE_ID)
        self.dump_attr(parts,self.name, self.BASE_NAME)
        self.dump_attr(parts,self.about, self.BASE_ABOUT)
        self.dump_attr(parts,self.url, self.BASE_URL)
        self.dump_attr(parts,self.version, self.BASE_VERSION)
        self.dump_attr(parts,json.loads(self.mbd_metadata), self.BASE_METADATA)
        return ",".join(parts)
    
    def get_metadata_json(self):
        return json.loads(self.mbd_metadata)
