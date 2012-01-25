import ConfigParser
import sys

def get_parm(key):        
    init_file_path = sys.argv[1]
    if init_file_path == None:
        raise "Please supply a file path to an .ini file"
    server_config = ConfigParser.ConfigParser()
    server_config.read(init_file_path)
    return server_config.get('general', key)
