import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii

#import submodules
from pcap_globals import *


def get_ipv4_info(pkt_data):

    pkt_info = {}

    #IPv4 header from https://tools.ietf.org/html/rfc791
    # 0                   1                   2                   3
    #0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|Version|  IHL  |Type of Service|          Total Length         |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|         Identification        |Flags|      Fragment Offset    |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|  Time to Live |    Protocol   |         Header Checksum       |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|                       Source Address                          |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|                    Destination Address                        |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   #|                    Options                    |    Padding    |
   #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    #                Example Internet Datagram Header

    try:
      iph = unpack('!BBHHHBBH4s4s', pkt_data[:20])

      version_ihl = iph[0]
      version     = version_ihl >> 4
      ihl         = version_ihl & 0xF
      iph_length  = ihl * 4

      tos         = iph[1]
      total_len   = iph[2]
      ip_id       = iph[3]
      flags       = (iph[4] & 0xE000) >> 13
      frag_offset = (iph[4] & 0x1FFF)

      ttl      = iph[5]
      protocol = iph[6]
      checksum = iph[7]
      s_addr   = socket.inet_ntoa(iph[8]);
      d_addr   = socket.inet_ntoa(iph[9]);

      pkt_info['ip_ver']       = version
      pkt_info['iph_length']   = iph_length
      pkt_info['tos']          = tos
      pkt_info['total_length'] = total_len 
      pkt_info['ip_id']        = ip_id
      pkt_info['flags']        = flags
      pkt_info['frag_offset']  = frag_offset
      pkt_info['is_frag']      = True if frag_offset != 0 or flags == 1 else False
      pkt_info['ttl']          = ttl
      pkt_info['protocol']     = protocol
      pkt_info['checksum']     = checksum
      pkt_info['s_addr']       = s_addr
      pkt_info['d_addr']       = d_addr
    except Exception, e:
      print 'Exception while parsing ipv4 header: ' + str(e)
      pkt_info['error'] = str(e)

    return pkt_info


