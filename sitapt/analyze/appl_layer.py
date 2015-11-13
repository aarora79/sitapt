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

#import submodules
from globals import globals
from utils import sa_logger
from wrangle import dbif
from wrangle.pcap import appl

#global varialbes for this file


logger = sa_logger.init(globals.PACKAGE_NAME)

def get_appl_layer_info(db_name, coll_name):
    #create a pipeline to get all the information we need
    #first we need network layer protocol information by packets and then by bytes
    ppln = [{'$group': {'_id': '$appl.appl', 'count': {'$sum': 1}, 'bytes': {'$sum': '$meta.orig_len'} } }]

    #run the pipeline, the results are in a cursor
    status, error_text, cs = dbif.db_run_pipeline(db_name, coll_name, ppln)

    #go through the cursor and total up the bytes and pkt count
    total_bytes = 0
    total_count = 0
    appl_info_list = []
    for doc in cs:
        total_bytes += doc['bytes']
        total_count += doc['count']

        appl_info_dict = {}
        appl_info_dict['protocol'] = doc['_id']
        appl_info_dict['pkts']     = doc['count']
        appl_info_dict['bytes']    = doc['bytes']

        #to be calculated in the next step
        appl_info_dict['pkts_percentage'] = 0.0
        appl_info_dict['bytes_percentage'] = 0.0

        #append to list
        appl_info_list.append(appl_info_dict)


    #go over one more time to add a count % and bytes %
    for  appl_info in appl_info_list:
        appl_info['pkts_percentage'] = float(appl_info['pkts']*100)/total_count
        appl_info['bytes_percentage'] = float(appl_info['bytes']*100)/total_bytes

    logger.info(appl_info_list)
    return appl_info_list


def get_quic_info(db_name, coll_name):


    #map reduce to find out the count of packets for each packet size
    mapper = Code("""
              function () {
                if (this.transport.protocol == "UDP" && (this.transport.src_port == 443 || this.transport.dest_port == 443))
                {
                    emit("quic_pkts", 1); 
                    emit("quic_bytes", this.network.total_length); 
                    emit("total_pkts", 1); 
                    emit("total_bytes", this.network.total_length);      
                }  
                else
                {
                    emit("total_pkts", 1); 
                    emit("total_bytes", this.network.total_length);  
                }
               }
               """)
    reducer = Code("""
                function (key, values) {
                  
                  return Array.sum(values);
                }
                """)
    status, error_text, coll = dbif.db_do_mapreduce(db_name, coll_name, mapper, reducer, 'quic_info')

    quic_info = {}
    for doc in coll.find():
        print doc
        quic_info[doc['_id']] = int(doc['value'])
    
    quic_info['pkts_percentage'] = (quic_info['quic_pkts'] * 100.0) / quic_info['total_pkts']
    quic_info['bytes_percentage'] = (quic_info['quic_bytes'] * 100.0) / quic_info['total_bytes']

    logger.info(quic_info)
    return quic_info



  