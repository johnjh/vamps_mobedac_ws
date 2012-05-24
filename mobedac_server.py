import cherrypy
from sqlalchemy import *
import MySQLdb
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from restresource import RESTResource
from projectorm import ProjectORM
from sampleorm import SampleORM
from libraryorm import LibraryORM
from sequencesetorm import SequenceSetORM
from submissionorm import SubmissionORM
from submission_detailsorm import SubmissionDetailsORM
from rest_log import mobedac_logger,set_error_file_logging_debug,set_error_file_logging_info
import logging
from submission_processor import Submission_Processor
from dbconn import Session, vampsSession
import sys
import traceback


class Root(object):
    
    # we no long need to register REST http listeners for project, sample, library and sequence set 
    # since this service only does processing of requests from mobedac...we no longer support
    # the retrieval of projects, samples, libraries, seq sets because all of that resides on mobedac...why
    # should we store it too???
#    project = RESTResource(ProjectORM)
#    sample = RESTResource(SampleORM)
#    library = RESTResource(LibraryORM)
#    sequenceset = RESTResource(SequenceSetORM)

    # register a url that would look like:    http://<host:port>/<base path>/submission
    submission = RESTResource(SubmissionORM)
    
    # we don't need to expose this url to the outside world either...http://<host:port>/<base path>/submission_details
#    submissiondetails = RESTResource(SubmissionDetailsORM)

    def __init__(self, submission_processor_thread):
        self.submission_processor_thread = submission_processor_thread

    # all of these @cherrypy.expose are annotations on these methods
    # that means you can tack them onto the end of the base path on VAMPS and it will do something
    # like http://<host:port>/<base path>/log_level_debug  will turn the logging to debug

    @cherrypy.expose
    def default(self, *args):
        cherrypy.response.status = 404
        mobedac_logger.debug("Likely got a bad URL with tuple path:  /" + "/".join(list(args)))
        return "Unknown resource /" + "/".join(list(args))

    @cherrypy.expose
    def index(self):
        return "MBL-JBPC VAMPS-MoBEDAC REST Service"

    @cherrypy.expose
    def log_level_debug(self):
        set_error_file_logging_debug()
        
    @cherrypy.expose
    def log_level_info(self):
        set_error_file_logging_info()

    @cherrypy.expose
    def halt_processor(self):
        self.submission_processor_thread.disable_processing()
    @cherrypy.expose
    def start_processor(self):
        self.submission_processor_thread.enable_processing()

    # this is exposes a url to the world to actually stop the server
    # http://<host:port>/<base path>/stop_the_server will do just that!!! it takes about 30 seconds before it quits
    # so give it time!!
    @cherrypy.expose
    def stop_the_server(self):
        try:
            mobedac_logger.debug("Telling submission processing thread to shutdown...")
            self.submission_processor_thread.stop_processing()
            # wait here for the processor to stop
            self.submission_processor_thread.join(20.0)
            # did it stop? do we need to to whack it?
            if self.submission_processor_thread.is_alive():
                self.submission_processor_thread.stop_processing()
        except:
            mobedac_logger.exception("Got error trying to stop submission processor thread")
        cherrypy.engine.exit()

if __name__ == '__main__':
    import argparse
    the_root = None
    try:
        from initparms import get_parm
        
        port = get_parm('port')
        logicalpath = get_parm('logicalpath')
        workingfiledir = get_parm('workingfiledir')

        mobedac_logger.debug("in main of mobedac_server")

        submission_processor_thread = Submission_Processor(10, get_parm('vamps_data_post_url'), get_parm('vamps_data_gast_url'), workingfiledir)
        # do we want to not start listening to requests on startup
        disable_processor_flag = get_parm("processor_disabled_on_startup")
        if disable_processor_flag != None and disable_processor_flag.lower() == 'true':
            submission_processor_thread.disable_processing()
        submission_processor_thread.start()
        # force cherrypy to use the port WE want
        cherrypy.config.update({'server.socket_port': int(port),})
        
        the_root = Root(submission_processor_thread)
        cherrypy.tree.mount(the_root, logicalpath)
        cherrypy.engine.start()
        cherrypy.engine.block()  # we don't return from this call...cherrypy takes over and starts handling requests
        the_root.stop_the_server()

    except:
        print "Error on startup"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit()



