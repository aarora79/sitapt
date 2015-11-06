import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii
import ipaddress

#import submodules
from pcap_globals import *


def get_ipv6_info(pkt_data):

    pkt_info = {}

    #IPv6 header from https://www.ietf.org/rfc/rfc2460.txt

    #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    #|Version| Traffic Class |           Flow Label                  |
    #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    #|         Payload Length        |  Next Header  |   Hop Limit   |
    #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    #|                                                               |
    #+                                                               +
    #|                                                               |
    #+                         Source Address                        +
    #|                                                               |
    #+                                                               +
    #|                                                               |
    #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    #|                                                               |
    #+                                                               +
    #|                                                               |
    #+                      Destination Address                      +
    #|                                                               |
    #+                                                               +
    #|                                                               |
    #+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    #                Example Internet Datagram Header

    try:
        iph = unpack('!IHH16s16s', pkt_data[:40])

        ver_tc_flowlabel = iph[0]
        version     = ver_tc_flowlabel >> 28
        tc          = (ver_tc_flowlabel & 0xFFFFFFF) >> 20
        flow_label  = (ver_tc_flowlabel & 0xFFFFF)

        total_len   = iph[1]

        nexthdr_hoplimit = iph[2]
        next_hdr         = nexthdr_hoplimit >> 4
        hop_limit        = nexthdr_hoplimit & 0x0F

        s_addr   = str(ipaddress.IPv6Address(iph[3]))
        d_addr   = str(ipaddress.IPv6Address(iph[4]))

        pkt_info['ip_ver']        = version
        pkt_info['traffic_class'] = tc
        pkt_info['flow_label']    = flow_label
        pkt_info['total_length']  = total_len 
        pkt_info['next_hdr']      = next_hdr
        pkt_info['protocol']      = next_hdr #stick in the protocol also for compatibility with parsing code for IPv4
        pkt_info['hop_limit']     = hop_limit
        pkt_info['s_addr']        = s_addr
        pkt_info['d_addr']        = d_addr
        pkt_info['is_frag']       = True if next_hdr == 44 else False
    except Exception, e:
        print 'Exception while parsing ipv6 header: ' + str(e)
        pkt_info['error'] = str(e)
   
    return pkt_info


