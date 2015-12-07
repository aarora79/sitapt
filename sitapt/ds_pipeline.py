# -*- coding: utf-8 -*-
#!/usr/bin/env python
#title           :ds_pipeline.py
#description     :Top level file for data science pipeline module in the SITAPT package
#author          :aarora79
#date            :20151003
#version         :0.1
#usage           :python ds_pipeline.py
#notes           :
#python_version  :2.7.10
#==============================================================================
import os
import sys
import argparse
import pkg_resources  # part of setuptools
#import submodules
from ingest import ingest
from globals import globals
from utils import sa_logger
from ingest import ingest
from wrangle import wrangle
from wrangle import dbif
from analyze import analyze
from visualize import visualize_and_analyze
#global varialbes for this file

#functions in the this module

def run_ds_pipeline(config):
    #get logger object, probably already created
    logger = sa_logger.init(globals.PACKAGE_NAME)
    logger.info('Data science pipeline begining...')

    #initialize db
    dbif.db_init()

    if config['action']['ingest']['make_list'] == True:
        #begin with data ingestion
        ingest.ingest_data(config)
    else:
        print 'skipping ingestion...'

    if config['action']['wrangle']['transform'] == True:
        #time for data wrangling
        wrangle.wrangle_data(config)
    else:
        logger.info('skipping wrangling and insertion of data into db ...')

    if config['action']['analyze']['analyze'] == True:
        #time for data analysis
        analyze.analyze_data(config)
    else:
        logger.info('skipping analysis ...')

    if config['action']['visualize']['visualize'] == True:
        #time for data visualization
        visualize_and_analyze.visualize_data(config)
    else:
        logger.info('skipping visualization ...')
    