import os
import sys
import argparse
import pkg_resources  # part of setuptools
import socket
from struct import *
import binascii
import json

#import submodules
from pcap_globals import *
import network
import transport
import appl

#global varialbes for this file

#logger = sa_logger.init(globals.PACKAGE_NAME)

def _get_pcap_header(pcap_header):

    hdr_as_dict =   {   'magic_number': socket.ntohl(pcap_header[0]),
                        'version_major': socket.ntohs(pcap_header[1]),
                        'version_minor': socket.ntohs(pcap_header[2]),
                        'thiszone': socket.ntohs(pcap_header[3]),
                        'sigfigs':  socket.ntohs(pcap_header[4]),
                        'snaplen': socket.ntohs(pcap_header[5]),
                        'network': socket.ntohs(pcap_header[6])
                }
    return hdr_as_dict

def _get_pcap_rec_header(pcap_rec_header):

    rec_hdr_as_dict = { 'ts_sec' :  socket.ntohl(pcap_rec_header[0]),
                        'ts_usec':  socket.ntohl(pcap_rec_header[1]),
                        'incl_len': socket.ntohl(pcap_rec_header[2]),
                        'orig_len': socket.ntohl(pcap_rec_header[2])
                 }
    return rec_hdr_as_dict

def _get_pkt_info(pkt_data, pcap_rec_header, dl_hdr):

    status = PCAP_FILE_OK
    pkt_info = {}
    network_info   = {}
    transport_info = {}
    app_info       = {} 
    other_info     = {} #empty for now
    
    network_info   = network.get_network_info(pkt_data)
    if 'error' not in network_info.keys():
        ip_hdr_len = 20 if network_info['ip_ver'] else 40
        protocol = network_info['protocol'] if network_info['ip_ver'] == 4 else network_info['next_hdr']
        #skip to transport layer data
        transport_info = transport.get_transport_info(network_info, pkt_data[ip_hdr_len:])
        if 'error' not in transport_info.keys():
            #provide the port number to the application layer
            app_info = appl.get_appl_info(network_info, transport_info, pkt_data[ip_hdr_len:])
            if 'error' in app_info.keys():
                print 'appl error'
                status = PCAP_FILE_PKT_ERROR
        else:
            status = PCAP_FILE_PKT_ERROR
    else:
        status = PCAP_FILE_PKT_ERROR
    

    #aggregate everything in pkt_info dictionary
    pkt_info['meta']      = pcap_rec_header
    pkt_info['datalink']  = dl_hdr
    pkt_info['network']   = network_info
    pkt_info['transport'] = transport_info
    pkt_info['appl']      = app_info
    pkt_info['other']     = other_info

    return status, pkt_info

def get_next_packet(file_handle):
    #read the packet, before the actual bytes there is timestamp info
    status = PCAP_FILE_OK
    pcap_rec_header = 0
    pkt_info = 0
    bytes_read = file_handle.read(PCAP_FILE_REC_HDR_LEN)
    count_of_bytes_read = len(bytes_read)
    if count_of_bytes_read == PCAP_FILE_REC_HDR_LEN:
        #header read successfully, now parse it
        #pcaprec header looks like this, from https://wiki.wireshark.org/Development/LibpcapFileFormat
        #typedef struct pcaprec_hdr_s {
        #guint32 ts_sec;         /* timestamp seconds */
        #guint32 ts_usec;        /* timestamp microseconds */
        #guint32 incl_len;       /* number of octets of packet saved in file */
        #guint32 orig_len;       /* actual length of packet */
        #} pcaprec_hdr_t;
        try:
            #parse the pcap rec header
            pcap_rec_header = unpack('!IIII', bytes_read)
            pcap_rec_header = _get_pcap_rec_header(pcap_rec_header)

            #now parse the packet itself
            pkt_len_incl_in_file = pcap_rec_header['incl_len']
            bytes_read = file_handle.read(pkt_len_incl_in_file)
            count_of_bytes_read = len(bytes_read)
            if count_of_bytes_read != pkt_len_incl_in_file:
                print 'could not read packet, read only ' + str(count_of_bytes_read) + ' bytes, expected to read ' + str(PCAP_FILE_REC_HDR_LEN)
                status = PCAP_FILE_ERROR
            else:
                dl_hdr = {'type': PCAP_FILE_DATALINK_RAW}
                try:
                    status, pkt_info = _get_pkt_info(bytes_read, pcap_rec_header, dl_hdr)
                    #pkt_info        = json.dumps(pkt_info)
                    #pcap_rec_header = json.dumps(pcap_rec_header)
                except Exception,e:
                    print 'Exception while getting packet info ' + str(e)
                    status = PCAP_FILE_PKT_ERROR
        except Exception, e:
            print 'Exception while parsing pcap rec header: ' + str(e)
            status = PCAP_FILE_ERROR
    else:
        if count_of_bytes_read == 0:
            print 'reached end of file...'
            status = PCAP_FILE_EOF_REACHED
        else:    
            print 'could not read pcap rec header, read only ' + str(count_of_bytes_read) + ' bytes, expected to read ' + str(PCAP_FILE_REC_HDR_LEN)
            status = PCAP_FILE_ERROR
        
    return status, pcap_rec_header, pkt_info

def open_pcap_file(name):
    file_handle = 0
    pcap_header = 0
    if os.path.exists(name):
        file_handle = open(name, 'rb')
        #read the pcap file header
        bytes_read = file_handle.read(PCAP_FILE_HEADER_LEN)
        count_of_bytes_read = len(bytes_read)
        if count_of_bytes_read == PCAP_FILE_HEADER_LEN:
            #header read successfully, now parse it
            #pcap header looks like this, from https://wiki.wireshark.org/Development/LibpcapFileFormat
            #typedef struct pcap_hdr_s {
            #guint32 magic_number;   /* magic number */
            #guint16 version_major;  /* major version number */
            #guint16 version_minor;  /* minor version number */
            #gint32  thiszone;       /* GMT to local correction */
            #guint32 sigfigs;        /* accuracy of timestamps */
            #guint32 snaplen;        /* max length of captured packets, in octets */
            #guint32 network;        /* data link type */
            #} pcap_hdr_t;
            try:
                pcap_header = unpack('!IHHIIII', bytes_read)
                pcap_header = _get_pcap_header(pcap_header)
            except OverflowError, e:
                #check if we hit the python bug where it reads the first 24 bytes incorrectly
                # it reads '\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xffe\x00\x00\x00'
                #the \xffe messes up the python int so it reports an overflow exception, ignore that and continue
                #parsing the file as a raw packet file (best guess)

                print 'ignored file header parsing bug (overlfow error with python int)'
                return PCAP_FILE_OK, file_handle, pcap_header

            except Exception, e:
                print 'Exception while parsing pcap header: ' + str(e)
                return PCAP_FILE_ERROR, file_handle, pcap_header
        else:
            print 'could not read header, read only ' + str(count_of_bytes_read) + ' bytes, expected to read ' + str(PCAP_FILE_HEADER_LEN)
            return PCAP_FILE_ERROR, file_handle, pcap_header
    else:
        print('file ' + name + ' does not exist')
        return PCAP_FILE_ERROR, file_handle, pcap_header
    return PCAP_FILE_OK, file_handle, pcap_header

if __name__ == '__main__':
    #main program starts here..
    #open_pcap_file('1.pcap') 
    status, file_handle, pcap_file_header = open_pcap_file('test4.pcap')
    print pcap_file_header
    counter = 0
    exception_count = 0
    #keep going until the end of file was reached or until there is a file error
    #pkt errors are ignored
    while status != PCAP_FILE_ERROR and status != PCAP_FILE_EOF_REACHED:
        #get next packet
        status, pcap_rec_info, pkt_info = get_next_packet(file_handle)

        counter += 1
        if status != PCAP_FILE_OK:
            exception_count += 1
            print 'pkt number #' + str(counter) + ' had an exception'
        else:
            print pkt_info
            t = pkt_info
            if t['appl']['appl'] != 'TCP' and t['appl']['appl'] != 'UDP':
                print t['appl']['appl']
        #print  str(counter) 
    print 'parsed ' + str(counter) + ' packets from this file. ' + str(exception_count) + ' packets had an exception.'
