import sys, traceback
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
import json as json 
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import Column, Integer, String
import httplib, urllib
from unidecode import unidecode
from initparms import get_parm
from object_retrieval_exception import ObjectRetrievalException


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
        complete_url = ""
        try:
            # dev mode?
            if get_parm("remote_objects_are_local").lower() == 'true':
                new_obj = cls.get_instance(id, sess_obj)
                if new_obj == None:
                    raise ObjectRetrievalException("Unable to retrieve object: " + id + " from db");
            else:
                headers = {'content-type': 'application/json'}
                conn = httplib.HTTPConnection(get_parm("mobedac_host"))
                object_path = cls.get_REST_sub_path()
                complete_url = get_parm("mobedac_base_path") + object_path + "/" + id + "?auth=" + get_parm("mobedac_auth_key")
                conn.request("GET", complete_url)
                response = conn.getresponse()
                data = response.read()
                # if all went ok then build an object
                if response.status != httplib.OK:
                    raise ObjectRetrievalException("Unable to retrieve object: " + id + " from host: " + get_parm('mobedac_host') + " url: " + complete_url)
                new_obj = cls({})
                decoded_data = unidecode(data)
                json_obj = json.loads(decoded_data)
                new_obj.from_json(True, json_obj, sess_obj)
            return new_obj
        except ObjectRetrievalException as ore:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)   
            raise ore
        except Exception as e:
            raise ObjectRetrievalException("Unable to retrieve object: " + id + " from host: " + get_parm('mobedac_host') + " url: " + complete_url + " error: " + str(e))

        
        finally:
            if conn != None:
                conn.close() 
            
    
    @classmethod
    def query(self, vpath):
        pass
        
    @classmethod
    def get_all(self,sess):
        try:
            obj_strs = []
            for row in sess.query(self).order_by(self.id).all():
                obj_strs.append(('"%s" :' % row.id) + ("{%s}" % row.to_json(sess)))
            return ",\n".join(obj_strs)
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
