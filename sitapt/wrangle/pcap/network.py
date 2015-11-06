import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii

#import submodules
from pcap_globals import *
import ipv4
import ipv6



def get_network_info(pkt_data):
    pkt_info = {}
    # the first thing to do is to check version number, ipv4 or ipv6 an then parse the packet accordingly
    iph = unpack('!B', pkt_data[:1])

    version_ihl = iph[0]
    version     = version_ihl >> 4
    
    if version == 4:
        pkt_info = ipv4.get_ipv4_info(pkt_data)
    elif version == 6:
        pkt_info = ipv6.get_ipv6_info(pkt_data)
    else:
        print 'unrecognized IP version ' + str(version)   
        pkt_info['error'] = PCAP_UNRECOGNIZED_IP_VER     

    return pkt_info




