# -*- coding: utf-8 -*-
#!/usr/bin/env python
#title           :sitapt.py
#description     :Top level file for sitapt.py module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python sitapt.py
#notes           :
#python_version  :2.7.10
#==============================================================================
import os
import sys
import argparse
import pkg_resources  # part of setuptools
import json
#import submodules
from ingest import ingest
from globals import globals
from utils import sa_logger
import ds_pipeline


#global varialbes for this file
#dictionary holding the configuration parameters
config = { 'version': globals.PACKAGE_VER, 'action':
                                            {'ingest':    { 'make_list': False, 'download': False}, 
                                             'wrangle':   { 'transform': False},
                                             'analyze':   { 'create_analysis_db': False, 'analyze': False},
                                             'visualize': { 'visualize': False}
                                            }
         }

#config['version'] = pkg_resources.require(globals.PACKAGE_NAME)[0].version


if __name__ == '__main__':
    #main program starts here..    
    #check usage
    banner = '------------ SITAPT, v' + config['version'] +' -----------'
    parser = argparse.ArgumentParser(__file__, description=banner)
    parser.add_argument('-a','--action',      default=globals.DEFAULT_ACTION, nargs='*', help='Action: complete|everything-except-ingestion.', required=False)
    parser.add_argument('-c','--credentials', default=globals.DEFAULT_CREDENTIALS, help='Credentials for authentication with the website from where the packet traces are being downloaded. This parameter is mandatory while specifying the \"complete\" or \"ingest-only\" option for the \"action\" parameter.', required=False)
    parser.add_argument('-u','--urllist',     default=globals.DEFAULT_WEBSITE_FOR_PACKET_TRACES, nargs='*', help='URL list for the top level pages from the website where the packet traces are being downloaded from. his parameter is mandatory while specifying the \"complete\" or \"ingest-only\" option for the \"action\" parameter.', required=False)
    parser.add_argument('-d','--downloaddir', default=globals.DEFAULT_DOWNLOAD_DIR, help='Directory to store downloaded packet trace files.', required=False)
    parser.add_argument('-w','--writetofile', default=globals.DEFAULT_WRITE_TO_FILE, help='Write to logs to specified file. Default behavior is to log to stdout', required=False)
    parser.add_argument('-m','--mode',        default=globals.DEFAULT_MODE, help='Whether to downlaod and analyze all files or just some (for example one file per month per year. Possible value are \"intense\", or \"light\", default is \"light\". Intense mode is currently not supported.', required=False)
    parser.add_argument('-t', '--tempdir',    default=globals.DEFAULT_TEMP_DIR,  help='Temporary directory for storing the data during the wrangling phase. This directory is cleared after the wrangling phase is over.', required=False)
    try:
        args = vars(parser.parse_args())
        #parse the action array and whatever action is found in the config['action'] set that to True
        for p in config['action'].keys():
            for s in config['action'][p].keys():
                if s in args['action']:
                    config['action'][p][s] = True

        config['credentials'] = args['credentials']
        config['urllist']     = args['urllist']
        config['downloaddir'] = args['downloaddir']
        config['writetofile'] = args['writetofile']
        config['file_extns_of_intrest'] = globals.DEFAULT_FILE_EXTNS_OF_INTREST
        config['mode']        = args['mode']
        config['tempdir']     = args['tempdir']

        #initialize logging        
        logger = sa_logger.init(globals.PACKAGE_NAME, sa_logger.INFO, config['writetofile'])
        logger.info(banner)
        logger.info('configuration in use is as follows:')
        logger.info(config)       

        #the default credentials are dummy, inform the user..
        if config['credentials'] == globals.DEFAULT_CREDENTIALS:
            logger.info('default credentials (' + globals.DEFAULT_CREDENTIALS + ') used, may not work....')
    except Exception, e:
        # not all parms supplied, exit from here. The argparse module would have printed the error message
        print 'Exception: ' + str(e)
        sys.exit()
    
    #initialization done, ready to start the data science pipeline
    logger.info('initialization done, ready to start the data science pipeline')
    ds_pipeline.run_ds_pipeline(config)