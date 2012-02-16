import cherrypy
import json as json
import traceback
import sys
from submissionorm import SubmissionORM
from unidecode import unidecode
from rest_log import mobedac_logger
from dbconn import Session

class RESTResource(object):
    orm_class = None
    
    def __init__(self, ormcls):
        self.orm_class = ormcls
        
    @cherrypy.expose
    def default(self, *vpath, **params):
        current_session = Session()
        try:
            method = getattr(self, "handle_" + cherrypy.request.method, None)
            if not method:
                methods = [x.replace("handle_", "")
                   for x in dir(self) if x.startswith("handle_")]
                cherrypy.response.headers["Allow"] = ",".join(methods)
                raise cherrypy.HTTPError(405, "Method not implemented.")
            return method(current_session, *vpath, **params)
        finally:
            current_session.close()

    def handle_GET(self, current_session, *vpath, **params):
        try:
            if len(vpath) == 0:
                all = self.orm_class.get_all(current_session)
                return all
            else:
                if "query" == vpath[0]:
                    # do a query to find children objects
                    query_class = vpath[1]
                    instance_id = vpath[2]
                    
                one = self.orm_class.get_instance(vpath[0], current_session)
                if one == None:
                    cherrypy.response.status = 404
                    return "Unable to find " + self.orm_class.mobedac_name() + " id: " + vpath[0]
                cherrypy.response.headers['content-type'] = 'application/json'
                result = "{%s}" % one.to_json(current_session)
                return result
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            cherrypy.response.status = 500
            return "There was an error attempting to service the request: " + str(e)
        
    def handle_POST(self, current_session, *vpath, **params):
        """ Create of an object
        """
        try:
            if self.orm_class is SubmissionORM:
                submission_obj = self.orm_class({})
                json_obj = self.json_from_body()
                submission_obj.from_json(True, json_obj, current_session)
                submission_obj.initialize_for_processing(current_session)                
                return str(submission_obj.id)
            else:
                # create the object
                new_obj = self.orm_class({})
                json_obj = self.json_from_body()
                new_obj.from_json(True, json_obj, current_session)
                current_session.add(new_obj)
                current_session.commit()
                return new_obj.id
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            current_session.rollback()
            cherrypy.response.status = 500
            return "There was an error on submission: " + e.value
        
    def handle_PUT(self, current_session, *vpath, **params):
        """ Update of an existing object
        """ 
        try:
            existing_obj = self.orm_class.get_instance(vpath[0], current_session)
            if existing_obj == None:
                cherrypy.response.status = 404
                return "Unable to find " + self.orm_class.mobedac_name() + " id: " + vpath[0]
            # update the object
            existing_obj.from_json(False, self.json_from_body(), current_session)
            current_session.commit()
            return "done Update of object: " + vpath[0]
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            cherrypy.response.status = 500
            current_session.rollback()
            return "An error occured processing your request: " + exc_value

    def handle_HEAD(self, current_session, *vpath, **params):
        try:
            if len(vpath) == 0:
                result = "false"
            else:
                one = self.orm_class.get_instance(vpath[0], current_session)
                if one == None:
                    result = "false"
                result = "true"
            cherrypy.response.headers['content-type'] = 'application/json'
            result_txt = '"result" : %s' % (result)
            return result_txt
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            cherrypy.response.status = 500
            return "There was an error attempting to service the request"
        
            
    def put_post_helper(self, vpath, params):
        pass
    
    def json_from_body(self):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        decoded_rawbody = unidecode(rawbody)
        json_obj = json.loads(decoded_rawbody)
        return json_obj

