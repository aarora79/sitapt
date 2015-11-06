#!/usr/bin/env python
#title           :wrangle.py
#description     :Top level file for wrangle.py module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python ingest.py
#notes           :
#python_version  :2.7.10
#==============================================================================
import os
import sys
import argparse
import pkg_resources  # part of setuptools
import wget
from bs4 import BeautifulSoup
import urlparse
from urlparse import urljoin
import shutil
import pickle
import pprint
import gzip
import json

#import submodules
from globals import globals
from utils import sa_logger
from pcap import sa_pcap
from pcap import pcap_globals
import dbif

#global varialbes for this file
RECORDS_IN_ONE_GO = 100000
GZ_EXTN           = '.gz'
logger = sa_logger.init(globals.PACKAGE_NAME)

#private functions in this module
##############################################################
# decompress_gz_file(input_file)
# This function decompresses the input .csv.gz file into a .csv
# file. The script exits if there is a failure during decompression.
# inputs: input_file name.
# returns: name of the csv file if decompression is successful.
def decompress_gz_file(input_file):
    output_file = ''
    try:
        logger.info('decompressing ' + input_file + '...this could take a few seconds....')
        sys.stdout.flush()
        with gzip.open(input_file, 'rb') as in_file:
            # uncompress the gzip_path INTO THE 's' variable
            s = in_file.read()

        # get original filename (remove 3 characters from the end: ".gz")
        uncompressed_path = input_file[:-3]
        
        # store uncompressed file data from 's' variable
        with open(uncompressed_path, 'wb') as out_file:
            out_file.write(s)
        logger.info('done decompressing ' + uncompressed_path + ' from ' + input_file)
    except Exception as e:
        logger.error('error while decompressing files from ' + input_file + ' error message [' + e.message + ']...')
        
    else:
        logger.info('file extraction completed...')
    return uncompressed_path

def _make_list_of_files_in_the_data_lake(config):
    dict_of_files = {}

    #get each file from the data lake, uncompress it, convert it into comsumable format and 
    #then store the consumable format in a database

    #start with copying and uncompressing the file        
    data_lake = config['downloaddir'] + '\\' + globals.PACKAGE_NAME + '\downloaded_files' 

    #look for folders and then for files inside those folders
    logger.info('looking for the files in the lake ' + data_lake)

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(data_lake):
        path = root.split('/')
        dir_name = os.path.basename(root)
        if dir_name not in dict_of_files.keys():
            dict_of_files[dir_name] = []
            
        for file in files:
            dict_of_files[dir_name].append(root + '\\' + str(file))

    logger.info('following files exist in the links, now going to process them one by one..')
    logger.info(dict_of_files)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dict_of_files)
    return dict_of_files

def extract_info_and_store_in_db(file_name):
    #read the file packet by packet and store it in mongo
    logger.info('about to begin file parsing and storge....' + file_name)
    status, file_handle, pcap_file_header = sa_pcap.open_pcap_file(file_name)
    logger.info(pcap_file_header)
    counter = 0
    exception_count = 0
    record_list =[]

    #create a collection in mongo
    last_slash = file_name.rfind('\\')
    db_collection_name = file_name[last_slash + 1:]

    dbif.db_create_collection(globals.DATA_COLLECTION_DB_NAME, db_collection_name)
    #keep going until the end of file was reached or until there is a file error
    #pkt errors are ignored
    while status != pcap_globals.PCAP_FILE_ERROR and status != pcap_globals.PCAP_FILE_EOF_REACHED:
        #get next packet
        status, pcap_rec_info, pkt_info = sa_pcap.get_next_packet(file_handle)

        counter += 1
        if status != pcap_globals.PCAP_FILE_OK:
            exception_count += 1
            logger.error('pkt number #' + str(counter) + ' had an exception')
        else:
            #dbif.db_add_record_to_collection(db_collection_name, pkt_info)
            record_list.append(pkt_info)
        if counter % RECORDS_IN_ONE_GO == 0:
            dbif.db_add_records_to_collection(globals.DATA_COLLECTION_DB_NAME, db_collection_name, record_list)
            record_list =[]
            logger.info('inserted pkt# ' + str(counter) + ' into DB')
    #insert pending records
    dbif.db_add_records_to_collection(globals.DATA_COLLECTION_DB_NAME, db_collection_name, record_list)

    logger.info('parsed ' + str(counter) + ' packets from this file. ' + str(exception_count) + ' packets had an exception.')
    logger.info('inserted everything into DB')


def _uncompress_files_and_extract_info(config, dict_of_files):

    #first copy over the file from the lake into a temp directory
    logger.info('now getting files from the lake and processing them')
    for key in dict_of_files.keys():
        #key is the year
        file_list = dict_of_files[key]

        for file_name in file_list:
            #copy the file
            logger.info('getting ' + file_name )
            bname = os.path.basename(file_name)
            shutil.copy2(file_name, config['tempdir'])
            #does it need to be uncompressed
            if GZ_EXTN == file_name[-3:]:
                uncompressed_file = decompress_gz_file(config['tempdir'] + '\\' + bname)
                #read the file and store it in a consumable format in the DB
                extract_info_and_store_in_db(uncompressed_file)


#public functions in the this module

def wrangle_data(config):
    #get logger object, probably already created
    logger.info('wrangling phase begining...')

    #first find out what all is in the lake
    dict_of_files = _make_list_of_files_in_the_data_lake(config)

    #ok now, copy over the files and uncompress them one by one
    _uncompress_files_and_extract_info(config, dict_of_files)