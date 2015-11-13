#!/usr/bin/env python
#title           :dbif.py
#description     :Top level file for db module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python dbif.py
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
from pymongo import MongoClient
from bson.son import SON

#import submodules
from globals import globals
from utils import sa_logger


#global varialbes for this file
MONGODB_HOSTNAME    = 'localhost'
MONGODB_PORT_NUMBER = 27017

REMOVE_IF_EXISTS = 'remove-if-exists'
DO_NOTHING_IF_EXISTS = 'do-nothing-if-collection-exists'

DBIF_OK    = 0
DBIF_ERROR = -1

DBIF_NAME = globals.PACKAGE_NAME

logger = sa_logger.init(globals.PACKAGE_NAME)

db_parms = {'initted': False }

def db_add_record_to_collection(db_name, collection_name, rec):
    status = DBIF_OK
    error_text = ''
    try:
        db_parms['client'][db_name][collection_name].insert_one(rec)
    except Exception,e:
        error_text = str(e)
        logger.error('Exception while inserting record ' + str(e))
        status = DBIF_ERROR
    return status, error_text

def db_add_records_to_collection(db_name, collection_name, records):
    status = DBIF_OK
    error_text = ''
    try:
        db_parms['client'][db_name][collection_name].insert(records)
    except Exception,e:
        error_text = str(e)
        logger.error('Exception while inserting records ')
        status = DBIF_ERROR
    return status, error_text

def db_create_collection(db_name, collection_name, behavior_if_exists = REMOVE_IF_EXISTS):
    status = DBIF_OK
    error_text = ''
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot create collection ' + collection_name
        logger.error(error_text)
        return DBIF_ERROR, error_text
    try:
        if behavior_if_exists == REMOVE_IF_EXISTS:
            #check if collection exists
            exists = collection_name in db_parms['client'][db_name].collection_names()
            if exists:
                logger.info('dropped collection ' + collection_name + ', creating new one by the same name')
                db_parms['client'][db_name][collection_name].drop()
        else:
            logger.info('skip collection name check since behavior_if_exists is' + behavior_if_exists)

        #now create new collection
        collection = db_parms['client'][db_name][collection_name]
    except Exception, e:
        error_text = str(e)
        logger.error('Exception while creating collection: ' + collection_name + ' : ' + str(e))
        status = DBIF_ERROR, error_text
    if status == DBIF_OK:
        logger.info('created collection ' + collection_name)
    return status, error_text

def db_init():
    status = DBIF_OK
    error_text = ''
    logger.info('begin with DB initialization..')
    try:
        client = MongoClient(MONGODB_HOSTNAME, MONGODB_PORT_NUMBER)
        logger.info('Mongo client created')
        db_parms['client'] = client        
        db_parms['initted'] = True
        logger.info('successfully opened connection to DB..')
    except Exception, e:
        logger.error('Exception occured while db_init: ' + str(e))
        status = DBIF_ERROR
    return status, error_text

def db_get_collection_names(db_name, name_filter = None):
    status = DBIF_OK
    error_text = ''
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + collection_name
        logger.error(error_text)
        return DBIF_ERROR, error_text

    if name_filter is None:
        name_list = db_parms['client'][db_name].collection_names()
    else:
        name_list = [coll_name for coll_name in db_parms['client'][db_name].collection_names() if name_filter in coll_name]

    return name_list

def db_collection_find_records(db_name, collection_name, filter_query):
    status = DBIF_OK
    error_text = ''
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + collection_name
        logger.error(error_text)
        return DBIF_ERROR, error_text

    #check if collection exists
    if collection_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + collection_name + ' does not exist in db, exiting..'
        logger.error(error_text)
        return DBIF_ERROR, error_text

    #read to query
    collection_to_query = db_parms['client'][db_name][collection_name]

    #find records
    records_cursor = collection_to_query.find(filter_query)
    num_records = records_cursor.count()

    logger.info('found ' + num_records + 'records in the collection that match the search criteria')
    return records_cursor, num_records

def db_get_collection_count(db_name, coll_name):
    count = 0
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + coll_name
        logger.error(error_text)
        return DBIF_ERROR, error_text, count

    #check if collection exists
    if coll_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + coll_name + ' does not exist in db, exiting..'
        logger.error(error_text)
        return DBIF_ERROR, error_text, count

    count = db_parms['client'][db_name][coll_name].count()
    return DBIF_OK, '', count
    
def db_run_pipeline(db_name, coll_name, ppln):
    cursor = ''
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + coll_name
        logger.error(error_text)
        return DBIF_ERROR, error_text, cursor

    #check if collection exists
    if coll_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + coll_name + ' does not exist in db, exiting..'
        logger.error(error_text)
        return DBIF_ERROR, error_text, cursor

    #ok ready to run pipeline
    cursor = db_parms['client'][db_name][coll_name].aggregate(ppln)
    return DBIF_OK, '', cursor

def db_get_all_records_in_collection(db_name, coll_name):
    cursor = ''
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + coll_name
        logger.error(error_text)
        return DBIF_ERROR, error_text, cursor

    #check if collection exists
    if coll_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + coll_name + ' does not exist in db, exiting..'
        logger.error(error_text)
        return DBIF_ERROR, error_text, cursor

    #ok ready to run pipeline
    cursor = db_parms['client'][db_name][coll_name].find()
    return DBIF_OK, '', cursor

def db_do_mapreduce(db_name, coll_name, mapper, reducer, output):
    result_coll = ''
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + coll_name
        logger.error(error_text)
        return DBIF_ERROR, error_text, result_coll

    #check if collection exists
    if coll_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + coll_name + ' does not exist in db, exiting..'
        logger.error(error_text)
        return DBIF_ERROR, error_text, result_coll

    #ok ready to run pipeline
    result_coll = db_parms['client'][db_name][coll_name].map_reduce(mapper, reducer, output)
    return DBIF_OK, '', result_coll

def db_is_doc_in_coll(db_name, coll_name, query):
    found = False
    #chek if db initted correctly
    if db_parms['initted'] == False:
        error_text = 'DB not yet initted, cannot query collection ' + coll_name
        logger.error(error_text)
        return found

    #check if collection exists
    if coll_name not in db_parms['client'][db_name].collection_names():
        error_text = 'Collection ' + coll_name + 'does not exist in db, exiting..'
        logger.error(error_text)
        return found

    #ok ready to run pipeline
    doc = db_parms['client'][db_name][coll_name].find_one(query)
    if doc != None:
        found = True
    return found


