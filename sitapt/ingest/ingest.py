#!/usr/bin/env python
#title           :ingest.py
#description     :Top level file for ingest.py module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python ingest.py
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

#import submodules
from globals import globals
from utils import sa_logger

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)
TEMP_DOWNLOAD_FILE = 'temp_download_file'
ANCHOR_TAG         = 'a'
PICKLE_FILE        = 'file_list.pickle'
list_of_files_to_download  = []
CAIDA_FILE_TIMESATMP_TOEKN = '.UTC'

#private functions in this module
def _download_progress_bar(c,t,w):    
    dots = (c*100)/t
    bar_str = '\r['
    for i in range(dots):
        bar_str += '='
    bar_str += '=>'
    for i in range(100-dots):    
        bar_str += ' '
    bar_str += ']%s%%' % dots
    print bar_str,
    if c == t:
        print ' '

def _convert_url_to_url_with_password(url, credentials):
    double_slash = url.find('//')
    user_and_pass = credentials + '@'
    url = url[:double_slash + 2] + user_and_pass + url[double_slash + 2:]
    return url

def _url_of_intrest(url, file_extns_of_intrest):
    #check if the file extension exists in the URL, we dont need a very strict check 
    # so the following code is ok
    result = [extn for extn in file_extns_of_intrest if extn in url]
    return True if len(result) else False    

def _make_list_of_download_candidates(page_url, links, downloaddir, file_extns_of_intrest):

    #now download files one by one
    logger.info('about to make a list of individual files from ' + page_url)
    logger.info('there are %d' %len(links) + ' links in ' + page_url)
    ctr = 1
    for link in links:
        download_link = link.get('href')
        #check if the link is a well formed url which can be downloaded
        if _url_of_intrest(download_link, file_extns_of_intrest) == True:
            #construct an absolute url
            download_link =urljoin(page_url, download_link)

            logger.info('adding[%d]==>' %ctr + download_link)
            list_of_files_to_download.append(download_link)
            ctr += 1
        else:
            logger.warning('skipping ' + download_link) 
            ctr += 1
        
def _parse_page_urls_and_make_url_list(url_list, credentials, downloaddir, file_extns_of_intrest):

    for url in url_list:
        if credentials != None:
            page_url = _convert_url_to_url_with_password(url, credentials)
        else:
            page_url = url

        logger.info('downloading ' + page_url)

        try:
            #remove any previously existing temp file, this is needed because if a file exists then
            #wget does some name mangling to create a file with a different name and then that would
            #need to be passed to BS4 and then ultimately that file would also be deleted, so just delete
            #before hand.
            if os.path.exists(TEMP_DOWNLOAD_FILE):
                os.remove(TEMP_DOWNLOAD_FILE)
            wget.download(page_url, TEMP_DOWNLOAD_FILE, bar = _download_progress_bar)
            soup = BeautifulSoup(open(TEMP_DOWNLOAD_FILE))

            links = soup.findAll(ANCHOR_TAG)

            _make_list_of_download_candidates(page_url, links, downloaddir, file_extns_of_intrest)
        except Exception, e:
            logger.error('Exception: ' + str(e))

def _parse_top_level_list(top_level_urls, credentials=None):

    #urllist to be returned from this function
    urllist = []
    logger.info('number of top level urls' + str(len(top_level_urls)))
    for url in top_level_urls:
        #add credentials if specified
        if credentials != None:
            page_url = _convert_url_to_url_with_password(url, credentials)
        else:
            page_url = url

        try:
            #if os.path.exists(TEMP_DOWNLOAD_FILE):
            #    os.remove(TEMP_DOWNLOAD_FILE)
            logger.info('downloading ' + page_url)
            if os.path.exists(TEMP_DOWNLOAD_FILE):
                os.remove(TEMP_DOWNLOAD_FILE)
            temp_file = wget.download(page_url, TEMP_DOWNLOAD_FILE, bar = _download_progress_bar)
            logger.info('stored content in temp files called ' + temp_file)
            soup = BeautifulSoup(open(temp_file))

            links = soup.findAll(ANCHOR_TAG)

            for link in links:
                download_link = link.get('href')
                #we are only intrested in directories, NOTE: CAIDA website specific, we are assuming two level parsing
                #maybe put this under config param
                if '/' in download_link:
                    download_link = urljoin(page_url, download_link)
                    #check if this is a parent directory, if so we want to ignore it
                    if download_link not in page_url:                    
                        urllist.append(download_link)
                    else:
                        logger.info('ignoring parent directory link ' + download_link)
            os.remove(temp_file)
        except Exception, e:
            logger.error('Exception: ' + str(e))

    logger.info('URL List :')
    logger.info(urllist)        
    return urllist        

def _create_dict_of_files_to_downlaod(config, list_of_files):
    dict_of_files_to_download = {}
    for file_url in list_of_files:
        #tokenize the file url
        # example https://data.caida.org/datasets/passive-2015/equinix-chicago/20150219-130000.UTC/equinix-chicago.dirA.20150219-130700.UTC.anon.pcap.gz
        groups = file_url.split('/')
        for token in groups:
            if CAIDA_FILE_TIMESATMP_TOEKN in token:
                #now we are looking at something like 20150219-130000.UTC, tokenize further
                yyyy = token[:4]
                mm   = token[4:6]
                dd   = token[6:8]
                #now check if this year month day exists in the dictionary
                if yyyy in dict_of_files_to_download.keys():
                    #it does
                    yyyy_dict = dict_of_files_to_download[yyyy]
                    #check if mm exists in yyyy
                    if mm in yyyy_dict.keys():
                        #it does
                        mm_dict = yyyy_dict[mm]
                        #check if dd exists in mm
                        if dd in mm_dict.keys():
                            #it does, increment the count of files for this year->month->day
                            dd_dict = mm_dict[dd]
                            dd_dict['count'] += 1
                        else:
                            #it does not, so create one
                            mm_dict[dd] = {}
                            mm_dict[dd]['count'] = 1
                    else:
                        #it does not, so create one
                        yyyy_dict[mm] = {}
                        #since this is new so it obviously does not contain a day
                        yyyy_dict[mm][dd] = {}
                        yyyy_dict[mm]['url'] = []
                        yyyy_dict[mm][dd]['count'] = 1
                        if config['mode'] == globals.LIGHT_MODE:
                            yyyy_dict[mm]['url'].append(file_url)

                else:
                    #it does not, so create one
                    dict_of_files_to_download[yyyy] = {}
                    #since this is new so it obviously does not contain a month or a day
                    dict_of_files_to_download[yyyy][mm] = {}
                    dict_of_files_to_download[yyyy][mm][dd] = {}
                    dict_of_files_to_download[yyyy][mm]['url'] = []
                    dict_of_files_to_download[yyyy][mm][dd]['count'] = 1 
                    if config['mode'] == globals.LIGHT_MODE:
                        dict_of_files_to_download[yyyy][mm]['url'].append(file_url)
                #we need only one token with timestap per URL    
                break    

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dict_of_files_to_download)
    return dict_of_files_to_download

def _download_files(config, dict_of_files_to_download):
    #traverse the dictionary by year->month and download files one by one
    logger.info('Begin packet capture files download...')
    for year in dict_of_files_to_download.keys():
        year_dict = dict_of_files_to_download[year]

        #we got the url now before downloading it make the directory to store it
        folder_name = year
        dir_name = config['downloaddir'] + '\\' + globals.PACKAGE_NAME + '\downloaded_files' + '\\' + folder_name
        logger.info('directory for downloaded files ' + dir_name)

        #first delete and then create the downloaded_files directory and all its subdirectories
        if os.path.exists(dir_name):
            logger.info(dir_name + ' exists...deleting it now and then creating it..')
            shutil.rmtree(dir_name)

        os.makedirs(dir_name, mode=0o777)    
        #move to directory where downloaded files are to be kept, but first save current working directory
        cwd = os.getcwd()
        os.chdir(dir_name)

        for month in year_dict.keys():
            month_dict = year_dict[month]
            #only download one file
            if config['mode'] == globals.LIGHT_MODE:
                url = month_dict['url'][0]
            else:
                logger.error('config file mode is ' + config['mode'] + ' but only light mode is supported')    
                url = month_dict['url'][0]
            #ready to download
            logger.info('Downloading packet capture file..............' + url)
            try:
                wget.download(url, bar = _download_progress_bar)
            except Exception,e:
                logger.error('Exception while downloading file ' + str(e))

            logger.info('Finished downloading packet capture file..............' + url)

            #go back to the original directory
        os.chdir(cwd)

#public functions in the this module

def ingest_data(config):
    #get logger object, probably already created
    logger.info('ingestion phase begining...')

    logger.info('parsing top level URL list to create a second level list..')

    #the CAIDA website requires two levels of parsing to reach the page with 
    #links to packet traces to download
    urllist = _parse_top_level_list(config['urllist'], config['credentials'])
  
    #2nd level parsing, this does not reuire passing credentials as urls generated from prev step already have crendentials
    urllist = _parse_top_level_list(urllist)

    #now ready for downloading trace files
    _parse_page_urls_and_make_url_list(urllist, None, config['downloaddir'], config['file_extns_of_intrest'])

    logger.info('there are a total of ' + str(len(list_of_files_to_download)) + ' files to download.')
    #pickle the file list to be downloaded, just in case we want to read it later on and start from there
    with open(PICKLE_FILE, 'w') as f:
        pickle.dump(list_of_files_to_download, f)
    logger.info('stored the file list in a pickle file called ' + PICKLE_FILE)

    #now arrange the files in a dictionary of year->month->day
    dict_of_files_to_download = _create_dict_of_files_to_downlaod(config, list_of_files_to_download)

    #ready to download the files, go for it...
    if config['action']['ingest']['download'] == True:
        _download_files(config, dict_of_files_to_download)
    else:
        print 'skipping download since action is ' + config['action']
 
   


