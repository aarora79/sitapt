#!/usr/bin/env python
#title           :analyze.py
#description     :Top level file for analyze.py module in the SITAPT package
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
import pandas as pd

#import submodules
from globals import globals
from utils import sa_logger
from wrangle import dbif
import network_layer as nl
import appl_layer as appl

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)

analysis_collection_list = ['applications', 'protocols', 'packet_size_distribution', 'quic_info']

#private functions in this module

def _get_metadata_about_coll(data_coll_db_name, coll_name):
    status = globals.ERROR
    meta_dict = {}
    #first extract info from coll name itself
    #name is of the form
    #equinix-chicago.dirA.20150219-125911.UTC.anon.pcap
    logger.info(coll_name)
    groups = coll_name.split('.')
    #at least  tokens should be there, equinix-chicago dirA 20150219-125911
    if len(groups) >= 3:
        #collection name is not of intrest
        #get to the timestamp portion
        ts = groups[2]
        #split it again
        groups = ts.split('-')
        if len(groups) != 0:
            year  = int(groups[0][:4])
            month = int(groups[0][4:6])
            quarter = (month - 1)/3 + 1
            day   = int(groups[0][6:8])

            status, error_text, count = dbif.db_get_collection_count(data_coll_db_name, coll_name)
            status = globals.OK
        else:
            logger.info('ignoring collection ' + coll_name + 'because ' + ts + 'does not contain \'-\'')
            return status, meta_dict
    else:
        logger.info('ignoring collection ' + coll_name + 'because it does not seem to be in the right format')
        return status, meta_dict

    #ok all information collected now put it in a dictionary to return
    meta_dict =  { 'name': coll_name, 'records': count, 'ts': { 'year': year, 'month': month, 'day': day, 'quarter': quarter} }
    return status, meta_dict


def _map_reduce_collection(data_coll_db_name, coll_name, data_analysis_db_name):
    #each collection's analysis is represented as a document in the resuls database
    #the results fb has collections for applications, protocols and packet size distribution

    #create an empty dictionary for storing the results
    info = {}
    #first get the meta data i.e. data about the collection itself rather than about what it contains
    logger.info('getting metadata about ' + coll_name)    
    status, meta = _get_metadata_about_coll(data_coll_db_name, coll_name)
    logger.info(meta)

    if status == globals.OK:
        info['meta'] = meta

        if dbif.db_is_doc_in_coll(data_analysis_db_name, 'quic_info', {"meta.name": coll_name}) != True:
            #get quic info 
            logger.info('adding quic information for ' + coll_name)
            info['items'] = appl.get_quic_info(data_coll_db_name, coll_name)
            dbif.db_add_record_to_collection(data_analysis_db_name, 'quic_info', (info))
        else:
            logger.info('document ' + coll_name + 'already exists in quic info table, skipping')

        if dbif.db_is_doc_in_coll(data_analysis_db_name, 'packet_size_distribution', {"meta.name": coll_name}) != True:
            #get packet size info
            logger.info('adding pktsize information for ' + coll_name)
            info['items'] = nl.get_pktsize_distribution_info(data_coll_db_name, coll_name)
            dbif.db_add_record_to_collection(data_analysis_db_name, 'packet_size_distribution', (info))
        else:
            logger.info('document ' + coll_name + 'already exists in packet_size_distribution table, skipping')

        if dbif.db_is_doc_in_coll(data_analysis_db_name, 'protocols', {"meta.name": coll_name}) != True:
            #get protcol info
            logger.info('adding network layer information for ' + coll_name)
            info['items'] = nl.get_network_layer_info(data_coll_db_name, coll_name)
            dbif.db_add_record_to_collection(data_analysis_db_name, 'protocols', (info))
        else:
            logger.info('document ' + coll_name + 'already exists in protocols table, skipping')

        if dbif.db_is_doc_in_coll(data_analysis_db_name, 'applications', {"meta.name": coll_name}) != True:
            #get application info
            logger.info('adding application layer information for ' + coll_name)
            info['items'] = appl.get_appl_layer_info(data_coll_db_name, coll_name)
            dbif.db_add_record_to_collection(data_analysis_db_name, 'applications', (info))
        else:
            logger.info('document ' + coll_name + 'already exists in applications table, skipping')



def _map_reduce_each_collection(data_coll_db_name, data_analysis_db_name):
    coll_names = dbif.db_get_collection_names(data_coll_db_name)
    for coll in coll_names:
        logger.info('analyzing collection ' + coll)
        _map_reduce_collection(data_coll_db_name, coll, data_analysis_db_name)
    logger.info('finished analysing collections in ' + data_coll_db_name)


def _get_df_for_protocol_data(coll_name):
    #iterate through the list of collections
    logger.info('converting ' + coll_name + ' to dataframe for easy analysis')
    status, error, cursor = dbif.db_collection_find_records(globals.ANALYSIS_DB_NAME, coll_name)
    #create a dataframe to hold the contents
    df = pd.DataFrame()
    count = 0
    if status == dbif.DBIF_OK:
        #read the documents one by one using the cursor
        for doc in cursor:
            nan_or_unassigned = 0.0
            df.loc[count, 'Date'] = str(doc['meta']['ts']['year']) + '-' + str(doc['meta']['ts']['month']) + '-' + str(doc['meta']['ts']['day'])
            for item in doc['items']:
                proto = str(item['protocol'])        
                #special handling for nan and unassigned (also handle the typo)
                if proto == 'nan' or proto == 'unassgined' or proto == 'unassigned':
                    nan_or_unassigned += float(item['pkts_percentage'])
                    #print 'count ' + str(count) + ' proto ' + proto + 'pkts percentage ' + str(nan_or_unassigned)
                    df.loc[count, 'unknown'] = nan_or_unassigned
                else:
                    df.loc[count, proto] = float(item['pkts_percentage'])
            count += 1

        #sort on the Date column
        df['Date'] = pd.to_datetime(df.Date)
        df = df.sort_values(by = 'Date')
        #the entire document set it in the dataframe now, not all documents had all the fields
        #replace NaNs with 0.0, this is because it makes sense to do this for pkts_percentage
        df = df.fillna(0.0)
        logger.info('created dataframe')
    else:
        logger.error('error while converting collection ' + coll + ' to dataframe')
    return status, df

def _get_df_for_pktsize_data(coll_name):
    #iterate through the list of collections
    logger.info('converting ' + coll_name + ' to dataframe for easy analysis')
    status, error, cursor = dbif.db_collection_find_records(globals.ANALYSIS_DB_NAME, coll_name)
    #create a dataframe to hold the contents
    df = pd.DataFrame()
    count = 0
    if status == dbif.DBIF_OK:
        #read the documents one by one using the cursor
        for doc in cursor:
            nan_or_unassigned = 0.0
            df.loc[count, 'Date'] = str(doc['meta']['ts']['year']) + '-' + str(doc['meta']['ts']['month']) + '-' + str(doc['meta']['ts']['day'])
            for item in doc['items']:
                label = str(item['start']) + '-' +  str(item['end'])
                df.loc[count, label] = float(item['count_percentage'])
            count += 1

        #sort on the Date column
        df['Date'] = pd.to_datetime(df.Date)
        df = df.sort_values(by = 'Date')
        #the entire document set it in the dataframe now, not all documents had all the fields
        #replace NaNs with 0.0, this is because it makes sense to do this for pkts_percentage
        df = df.fillna(0.0)
        logger.info('created dataframe')
    else:
        logger.error('error while converting collection ' + coll + ' to dataframe')
    return status, df

def _get_df_for_quic_data(coll_name):
    #iterate through the list of collections
    logger.info('converting ' + coll_name + ' to dataframe for easy analysis')
    status, error, cursor = dbif.db_collection_find_records(globals.ANALYSIS_DB_NAME, coll_name)
    #create a dataframe to hold the contents
    df = pd.DataFrame()
    count = 0
    if status == dbif.DBIF_OK:
        #read the documents one by one using the cursor
        for doc in cursor:
            df.loc[count, 'Date'] = str(doc['meta']['ts']['year']) + '-' + str(doc['meta']['ts']['month']) + '-' + str(doc['meta']['ts']['day'])

            df.loc[count, 'pkts_percentage'] = float(doc['items']['pkts_percentage'])
            df.loc[count, 'bytes_percentage'] = float(doc['items']['bytes_percentage'])
            count += 1

        #sort on the Date column
        df['Date'] = pd.to_datetime(df.Date)
        df = df.sort_values(by = 'Date')
        #the entire document set it in the dataframe now, not all documents had all the fields
        #replace NaNs with 0.0, this is because it makes sense to do this for pkts_percentage
        df = df.fillna(0.0)
        logger.info('created dataframe')
    else:
        logger.error('error while converting collection ' + coll + ' to dataframe')
    return status, df



def _read_data_from_db_to_dataframe(config):

    #iterate through the list of collections
    logger.info('iterating through the collections to convert them into dataframes for easy analysis')
    #for coll in analysis_collection_list:
    status, df = _get_df_for_protocol_data('protocols')
    if status == dbif.DBIF_OK:
        csv_file_name = 'protocols.csv'
        df.to_csv(csv_file_name)
        logger.info('written ' + csv_file_name)
    else:
        logger.error('error while converting \'protocols\' collection  to dataframe')

    status, df = _get_df_for_protocol_data('applications')
    if status == dbif.DBIF_OK:
        csv_file_name = 'applications.csv'
        df.to_csv(csv_file_name)
        logger.info('written ' + csv_file_name)
    else:
        logger.error('error while converting \'applications\' collection  to dataframe')

    status, df = _get_df_for_pktsize_data('packet_size_distribution')
    if status == dbif.DBIF_OK:
        csv_file_name = 'packet_size_distribution.csv'
        df.to_csv(csv_file_name)
        logger.info('written ' + csv_file_name)
    else:
        logger.error('error while converting \'packet_size_distribution\' collection  to dataframe')

    status, df = _get_df_for_quic_data('quic_info')
    if status == dbif.DBIF_OK:
        csv_file_name = 'quic_info.csv'
        df.to_csv(csv_file_name)
        logger.info('written ' + csv_file_name)
    else:
        logger.error('error while converting \'quic_info\' collection  to dataframe')

#public functions in the this module
def analyze_data(config):
    #get logger object, probably already created
    logger.info('analysis phase begining...')

    if config['action']['analyze']['create_analysis_db'] == True:
        logger.info('create_analysis_db set to True, checking which collections to be created new')
        #create db and tables
        for col in analysis_collection_list:
            dbif.db_create_collection(globals.ANALYSIS_DB_NAME, col, dbif.DO_NOTHING_IF_EXISTS)

        _map_reduce_each_collection(globals.DATA_COLLECTION_DB_NAME, globals.ANALYSIS_DB_NAME)

    #now read to analyse the data
    _read_data_from_db_to_dataframe(config)