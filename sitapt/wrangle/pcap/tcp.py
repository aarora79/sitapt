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


def get_tcp_info(network_info, pkt_data):
    pkt_info = {}
    try:
        #TCP header, from https://tools.ietf.org/html/rfc793
        #   TCP Header Format
        #0                   1                   2                   3
        #0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|          Source Port          |       Destination Port        |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|                        Sequence Number                        |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|                    Acknowledgment Number                      |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|  Data |           |U|A|P|R|S|F|                               |
        #| Offset| Reserved  |R|C|S|S|Y|I|            Window             |
        #|       |           |G|K|H|T|N|N|                               |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|           Checksum            |         Urgent Pointer        |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|                    Options                    |    Padding    |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #|                             data                              |
        #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        #                        TCP Header Format

        #we are not intrested in options so only parse first 20 bytes
        tcph = unpack('!HHLLBBHHH', pkt_data[:20])

        src_port  = (tcph[0])
        dest_port = (tcph[1])
        #rest of the fields are of no intrest to us but can be added if needed
        pkt_info['protocol']  = 'TCP'
        pkt_info['src_port']  = src_port
        pkt_info['dest_port'] = dest_port

    except Exception, e:
        pkt_info['protocol']  = 'TCP'
        #check if fragmented
        #print network_info
        if len(pkt_data) < 20 and not network_info['is_frag']:
            print 'Exception while parsing tcp header: ' + str(e) + ' [input pkt data len was ' + str(len(pkt_data)) + ']'
            pkt_info['error']     = str(e)
            
    return pkt_info
