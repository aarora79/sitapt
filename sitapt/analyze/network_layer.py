#!/usr/bin/env python
#title           :network_layer.py
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
from bson.code import Code
import pandas as pd

#import submodules
from globals import globals
from utils import sa_logger
from wrangle import dbif
from wrangle.pcap import appl

#global varialbes for this file
PKTSIZE_BIN_SIZE    = 100
MAX_PACKETSIZE_BINS = 16
MAX_POSSIBLE_PACKET_SIZE = 65535

logger = sa_logger.init(globals.PACKAGE_NAME)

def get_network_layer_info(db_name, coll_name):
    #create a pipeline to get all the information we need
    #first we need network layer protocol information by packets and then by bytes
    ppln = [{'$group': {'_id': '$network.protocol', 'count': {'$sum': 1}, 'bytes': {'$sum': '$meta.orig_len'} } }]

    #run the pipeline, the results are in a cursor
    status, error_text, cs = dbif.db_run_pipeline(db_name, coll_name, ppln)

    #go through the cursor and total up the bytes and pkt count
    total_bytes = 0
    total_count = 0
    nl_info_list = []
    for doc in cs:
        total_bytes += doc['bytes']
        total_count += doc['count']

        nl_info_dict = {}
        proto_name = appl.find_appl_for_ip_protocol(doc['_id'])
        nl_info_dict['protocol'] = proto_name if proto_name != 'unassigned' else str(doc['_id'])
        nl_info_dict['pkts']     = doc['count']
        nl_info_dict['bytes']    = doc['bytes']

        #to be calculated in the next step
        nl_info_dict['pkts_percentage'] = 0.0
        nl_info_dict['bytes_percentage'] = 0.0

        #append to list
        nl_info_list.append(nl_info_dict)


    #go over one more time to add a count % and bytes %
    for  nl_info in nl_info_list:
        nl_info['pkts_percentage'] = float(nl_info['pkts']*100)/total_count
        nl_info['bytes_percentage'] = float(nl_info['bytes']*100)/total_bytes

    logger.info(nl_info_list)
    return nl_info_list

def get_pktsize_distribution_info(db_name, coll_name):

    #create a distribution
    #create the first entry before starting the loop
    pktsize_bin = { 'start': 0, 'end': PKTSIZE_BIN_SIZE, 'count': 0, 'count_percentage': 0.0 }
    pktsize_distribution =[]
    pktsize_distribution.append(pktsize_bin)
    for i in range(MAX_PACKETSIZE_BINS - 1):
        pktsize_bin = { 'start': pktsize_distribution[i]['end'] + 1, 'end': pktsize_distribution[i]['end'] + PKTSIZE_BIN_SIZE, 'count': 0, 'count_percentage': 0.0 }
        pktsize_distribution.append(pktsize_bin)
    #make the last bin all the way to max packet size to cover all possible packet sizes
    pktsize_distribution[MAX_PACKETSIZE_BINS - 1]['end'] = MAX_POSSIBLE_PACKET_SIZE

    #map reduce to find out the count of packets for each packet size
    mapper = Code("""
              function () {
                emit(String(this.network.total_length), 1);        
               }
               """)
    reducer = Code("""
                function (key, values) {
                  
                  return Array.sum(values);
                }
                """)
    status, error_text, coll = dbif.db_do_mapreduce(db_name, coll_name, mapper, reducer, 'pktsize_distribution')

    total_count = 0
    for doc in coll.find():
        length = int(doc['_id'])
        index = length / PKTSIZE_BIN_SIZE;
        if length % PKTSIZE_BIN_SIZE == 0:
            index -= 1;
        if index >= MAX_PACKETSIZE_BINS:
            index = MAX_PACKETSIZE_BINS - 1
        pktsize_distribution[index]['count'] += int(doc['value'])
        total_count += int(doc['value'])

    #now calculate percentages
    for i in range(MAX_PACKETSIZE_BINS):
        pktsize_distribution[i]['count_percentage'] = (pktsize_distribution[i]['count'] * 100.0) / total_count
    
    logger.info(pktsize_distribution)
    return pktsize_distribution




