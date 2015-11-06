import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii

#import submodules
from pcap_globals import *
import tcp
import udp

#global varialbes for this file

#logger = sa_logger.init(globals.PACKAGE_NAME)


def get_transport_info(network_info, pkt_data):
    pkt_info = {}
    # check which protocol and handle accordingly
    protocol = network_info['protocol']
    if protocol == 6:
        pkt_info = tcp.get_tcp_info(network_info, pkt_data)
    elif protocol == 17:
        pkt_info = udp.get_udp_info(network_info, pkt_data)
    else:
        pkt_info ['protocol'] = str(protocol)

    return pkt_info
