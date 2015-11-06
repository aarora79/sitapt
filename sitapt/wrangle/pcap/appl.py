import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii
import pandas as pd
import numpy as np
#import submodules
from pcap_globals import *

#global varialbes for this file
#port list to application mapping file name, downloaded from the IANA website 
#http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
#file header is as follows
#Service Name    Port Number Transport Protocol  Description Assignee    Contact Registration Date   Modification Date   Reference   Service Code    Known Unauthorized Uses Assignment Notes

PORT_LIST_CSV_FILE_NAME = 'service-names-port-numbers.csv'
port_name_to_app_file_mapping_load_status = PCAP_FILE_OK
port_to_appl_mapping =  ['unassigned'] * 65536

#downloaded from http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
#file header is Decimal Keyword Protocol    IPv6 Extension Header   Reference
IP_PROTOCOL_LIST_CSV_FILE_Name = 'protocol-numbers-1.csv'
ip_protocol_list_csv_file_load_status = PCAP_FILE_OK

#load the csv for the port number to application mapping

try:
    dir_name = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(dir_name, PORT_LIST_CSV_FILE_NAME)
    port_list_df = pd.read_csv(file_name)
    #there are some Nan entries in the csv file, ignore them
    #store the port number and application names in an array indexed by port number itself
    for x in range(len(port_list_df)):
        info = port_list_df.iloc[x]
        port_num = str(info['Port Number'])
        #port number could just be a number, say 443, or it could be a range written as 654-675
        #but first check for 'nan', for some reason python thinks port number is a float so need to typecast
        if (port_num) == str(pd.np.nan):
            continue
        groups = port_num.split('-')
        if len(groups) == 1:
            #nothing to split, there was no '-'
            port_to_appl_mapping[int(port_num)] = info['Service Name']            
        else:
            start_port_num = int(groups[0])
            end_port_num   = int(groups[1])
            #print str(start_port_num)+'-'+str(end_port_num)
            for i in range(end_port_num - start_port_num):
                port_to_appl_mapping[start_port_num + i] = info['Service Name'] 
except Exception, e:
    print 'Exception while trying to open ' + file_name + ' file, ' + str(e)
    port_name_to_app_file_mapping_load_status = PCAP_FILE_ERROR


try:
    dir_name = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(dir_name, IP_PROTOCOL_LIST_CSV_FILE_Name)
    ip_protocol_list_df = pd.read_csv(file_name)
except Exception, e:
    print 'Exception while trying to open ' + file_name + ' file, ' + str(e)
    ip_protocol_list_csv_file_load_status = PCAP_FILE_ERROR


def _find_appl_for_port_and_proto(port, proto):
    #find application matching this port, this would return a list
    #appl_list  = port_list_df[(port_list_df['Port Number'] == str(port)) & (port_list_df['Transport Protocol'] == proto)]
    #return 'unassigned' if len(appl_list) == 0 else appl_list['Service Name'].iloc[0]

    #faster implementation
    #print proto
    if int(port) <= 65535:
        return port_to_appl_mapping[port]
    return 'unassigned'

def _find_appl_for_ip_protocol(proto):
    #find application matching this protocol, this would return a list
    # >= 142 is not used
    return 'unassgined' if proto >= 142 else ip_protocol_list_df.iloc[int(proto)]['Keyword']

def get_appl_info(network_header, transport_header, pkt_data):
    pkt_info = {}
    #check if the port list has been loaded successfully, if not then return empty
    if port_name_to_app_file_mapping_load_status != PCAP_FILE_OK:
        print 'failed to load ' + PORT_LIST_CSV_FILE_NAME
        pkt_info['error'] = 'failed to load ' + PORT_LIST_CSV_FILE_NAME
        return pkt_info

    if ip_protocol_list_csv_file_load_status != PCAP_FILE_OK:
        print 'failed to load ' + IP_PROTOCOL_LIST_CSV_FILE_Name
        pkt_info['error'] = 'failed to load ' + IP_PROTOCOL_LIST_CSV_FILE_Name
        return pkt_info

    # check which protocol and handle accordingly
    try:
        proto = network_header['protocol']
        if network_header['is_frag'] != True:
            if proto == 6 or proto == 17:
                src_port  = transport_header['src_port']
                dest_port = transport_header['dest_port']
            
                pkt_info['appl_based_on_src_port']  = _find_appl_for_port_and_proto(src_port, proto)
                pkt_info['appl_based_on_dest_port'] = _find_appl_for_port_and_proto(dest_port, proto)

                #overall application type is the one defined by whichever port is in the 1 to 1024 range
                #since the 1024 range is reserved. This is a best guess. If both ports are < 1024 the most likely
                #they are the same, if not then anyway the appl based on src and dest ports are included separately as well
                pkt_info['appl'] = pkt_info['appl_based_on_src_port'] if int(src_port) <= 1024  else pkt_info['appl_based_on_dest_port']
            else:
                #use the network layer protocol as the application
                pkt_info['appl'] = _find_appl_for_ip_protocol(proto)
        else:
            #use the network layer protocol as the application
            pkt_info['appl'] = _find_appl_for_ip_protocol(proto)

    except Exception,e:
        print 'Exception occured while adding application layer info: ' + str(e)
        pkt_info['error'] = str(e)

    return pkt_info

    