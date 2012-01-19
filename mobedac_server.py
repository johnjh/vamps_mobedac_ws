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
        usage = "usage: %prog [options] arg1 arg2"
        parser = argparse.ArgumentParser(description='MBL Sequence Pipeline')
        parser.add_argument('-p', '--port', required=False, metavar = 'PORT', 
                                                     help = 'Listen port', default=8080)
        parser.add_argument('-l', '--logicalpath',  required=False,          
                                                     help = 'Logical path root e.g. /vamps_mobedac_ws', default = '/')
        args = parser.parse_args()

        submission_processor_thread = Submission_Processor(10, "http://vampsdev.mbl.edu/uploads/upload_data_post.php", "http://vampsdev.mbl.edu/uploads/upload_data_gast.php", "/Users/johnhufnagle/Documents/workspace/mobedac_rest")
        submission_processor_thread.start()
        cherrypy.config.update({'server.socket_port': int(args.port),})
        the_root = Root(submission_processor_thread)
        cherrypy.quickstart(the_root, args.logicalpath)
        the_root.stop_the_server()

    except:
        print "Error on startup"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit()



