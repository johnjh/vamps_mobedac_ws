import cherrypy
import logging
from logging.handlers import RotatingFileHandler
from initparms import get_parm


log = cherrypy.log

def set_error_file_logging_debug():
    global mobedac_logger
    mobedac_logger.setLevel(logging.DEBUG)

def set_error_file_logging_info():
    global mobedac_logger
    mobedac_logger.setLevel(logging.INFO)

# Remove the default FileHandlers if present. 
log.error_file = "" 
log.access_file = "" 
maxBytes = getattr(log, "rot_maxBytes", 10000000) 
backupCount = getattr(log, "rot_backupCount", 10) 
# Make a new RotatingFileHandler for the error log. 
fname = getattr(log, "rot_error_file", get_parm("error_log_path")) 
h = RotatingFileHandler(fname, 'a', maxBytes, backupCount) 
h.doRollover()
h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")) 
log.error_log.addHandler(h) 

# Make a new RotatingFileHandler for the access log. 
fname = getattr(log, "rot_access_file", get_parm("access_log_path")) 
h = RotatingFileHandler(fname, 'a', maxBytes, 
backupCount) 
h.setFormatter(cherrypy._cplogging.logfmt) 
log.access_log.addHandler(h)

# this is to be what is visible
mobedac_logger = log.error_log
mobedac_logger.setLevel(logging.DEBUG)