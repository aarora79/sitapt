import logging

DEBUG   = logging.DEBUG
INFO    = logging.INFO
WARNING = logging.WARNING
FORMAT  = '%(asctime)s,%(name)s,%(levelname)s,%(filename)s,%(lineno)s,%(message)s'

module = {}
modules_using_logger = []

def _check_if_already_registered(module_name):
    for m in modules_using_logger:
        if m['name'] == module_name:
            return True, m
    return False, {}
            
def init(module_name='app', log_level=logging.INFO, write_to_file='sitapt.log'):

    #create a logger object for this application only if not already created
    #if module_name in modules_using_logger:
    #    raise saLoggerException('module \"' + module_name + '\" already registered')
    exists, module = _check_if_already_registered(module_name)
    if exists == True:        
        return module['logger_object']

    # create gw_logger
    gw_logger = logging.getLogger(module_name)
    gw_logger.setLevel(log_level)
    #gw_logger.basicConfig(format=FORMAT)

    # create console handler and set level to debug
    if write_to_file == None:
        ch = logging.StreamHandler(stream = None)
    else:
        f = open(write_to_file, 'w')
        ch = logging.StreamHandler(stream = f)

    ch.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter(FORMAT)

    # add formatter to ch
    ch.setFormatter(formatter)  

    # add ch to gw_logger
    gw_logger.addHandler(ch)

    #add to module list
    module = { 'name': module_name, 'logger_object': gw_logger}
    modules_using_logger.append(module)

    return gw_logger