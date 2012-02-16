import ConfigParser
import sys

environment = ""
if len(sys.argv) < 3:
    raise Exception("Please supply a run environment [development | test | production]")
environment = sys.argv[2]
if not(environment) or (environment != 'development' and environment != 'test' and environment != 'production'):
    raise Exception("Invalid command-line environment value: '" + environment + "'.  Please supply a valid run environment [development | test | production]")
print "**** Starting in environment: " + environment
def get_parm(key):        
    global environment
    init_file_path = sys.argv[1]
    if init_file_path == None:
        raise Exception("Please supply a file path to an .ini file")
    server_config = ConfigParser.ConfigParser()
    server_config.read(init_file_path)
    return server_config.get(environment, key)
