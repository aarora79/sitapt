import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii

#import submodules
from pcap_globals import *

#global varialbes for this file

#logger = sa_logger.init(globals.PACKAGE_NAME)


def get_udp_info(network_info, pkt_data):
    pkt_info = {}
    try:
        #udp header, from https://tools.ietf.org/html/rfc768
        #         0      7 8     15 16    23 24    31  
        #         +--------+--------+--------+--------+ 
        #         |     Source      |   Destination   | 
        #         |      Port       |      Port       | 
        #         +--------+--------+--------+--------+ 
        #         |                 |                 | 
        #         |     Length      |    Checksum     | 
        #         +--------+--------+--------+--------+ 
        #         |                                     
        #         |          data octets ...            
        #         +---------------- ...                 

        #              User Datagram Header Format

        udph = unpack('!HHHH', pkt_data[:8])
        src_port  = (udph[0])
        dest_port = (udph[1])
        #rest of the fields are of no intrest to us but can be added if needed
        pkt_info['protocol']  = 'UDP'
        pkt_info['src_port']  = src_port
        pkt_info['dest_port'] = dest_port
        
    except Exception, e:
        pkt_info['protocol']  = 'UDP'
        #check if fragmented
        if len(pkt_data) < 8 and not network_info['is_frag']:
            print 'Exception while parsing tcp header: ' + str(e) + ' [input pkt data len was ' + str(len(pkt_data)) + ']'
            pkt_info['error']     = str(e)
            
    return pkt_info
