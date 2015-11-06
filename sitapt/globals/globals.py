#!/usr/bin/env python
#title           :globals.py
#description     :Top level file for globals.py module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python globals.py
#notes           :
#python_version  :2.7.10
#==============================================================================

#package name, used by other modules for determining version number
PACKAGE_NAME = 'sitapt'
PACKAGE_VER  = '0.1.0'

LIGHT_MODE = 'light'

#--------------------------------------
#default for command line arguments
#--------------------------------------
#by default download packet traces from CAIDA website. Created as a list even though there is a single entry by default
DEFAULT_WEBSITE_FOR_PACKET_TRACES=['https://data.caida.org/datasets/passive-2015/equinix-chicago/20150521-130000.UTC/']

ACTION_EVERYTHING='complete'
ACTION_EVERYTHING_EXCEPT_INGESTION='everything-except-ingestion'
ACTION_MAKE_DOWNLOAD_FILELIST_ONLY='make-download-file-list-only'
#by default do everything i.e. ingestion and analysis
DEFAULT_ACTION=ACTION_EVERYTHING

#credentials for logging into the website for packet trace download. The default credentials are just place holders, wont work.
DEFAULT_CREDENTIALS='sitapt@sitapt.edu'

#by default download everything in the current directory from where this script is being run from
DEFAULT_DOWNLOAD_DIR='.'

#by default everything during the wrangling phase is stored here
DEFAULT_TEMP_DIR='.'

#by default log everything to stdout
DEFAULT_WRITE_TO_FILE=None

#file extensions of intrest (download files with these extensions)
DEFAULT_FILE_EXTNS_OF_INTREST = ['.pcap.gz']

#files to download and analyze, intense means download all files that are found by scraping the website, light means 
#one file per month per year
DEFAULT_MODE =  LIGHT_MODE

#DB names
ANALYSIS_DB_NAME = 'sitapt-analysis'
DATA_COLLECTION_DB_NAME = 'sitapt'

#generic return value from functions
OK='ok'
ERROR='error'

