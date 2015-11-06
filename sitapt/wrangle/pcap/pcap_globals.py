import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii

#import submodules



#global varialbes for this file
PCAP_FILE_OK              = 0
PCAP_FILE_ERROR           = -1
PCAP_FILE_EOF_REACHED     = -2
PCAP_FILE_PKT_ERROR       = -3
PCAP_FILE_HEADER_LEN      = 24
PCAP_FILE_REC_HDR_LEN     = 16
PCAP_FILE_DATALINK_RAW    = 101
PCAP_UNRECOGNIZED_IP_VER = 'unrecognized-ip-version'
PCAP_NO_ERROR            = 'no-error'

