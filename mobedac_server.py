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
    project = RESTResource(ProjectORM)
    sample = RESTResource(SampleORM)
    library = RESTResource(LibraryORM)
    sequenceset = RESTResource(SequenceSetORM)
    submission = RESTResource(SubmissionORM)
    submissiondetails = RESTResource(SubmissionDetailsORM)

    def __init__(self, submission_processor_thread):
        self.submission_processor_thread = submission_processor_thread

    @cherrypy.expose
    def index(self):
        return "JBPC VAMPS-MoBEDAC REST Service"

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

    @cherrypy.expose
    def stop_the_server(self):
        try:
            mobedac_logger.debug("Telling submission processing thread to shutdown...")
            submission_processor_thread.stop_processing()
            # wait here for the processor to stop
            submission_processor_thread.join(20.0)
            # did it stop? do we need to to whack it?
            if submission_processor_thread.is_alive():
                submission_processor_thread.stop_processing()
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
        disable_processor_flag = get_parm("processor_disabled_on_startup")
        if disable_processor_flag != None and disable_processor_flag.lower() == 'true':
            submission_processor_thread.disable_processing()
        submission_processor_thread.start()
        cherrypy.config.update({'server.socket_port': int(port),})
        the_root = Root(submission_processor_thread)
        cherrypy.quickstart(the_root, logicalpath)
        the_root.stop_the_server()

    except:
        print "Error on startup"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit()



