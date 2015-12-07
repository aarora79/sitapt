import os
import sys
import time
import argparse
import pkg_resources  # part of setuptools
from collections import OrderedDict
#import submodules
from globals import globals
from utils import sa_logger
import charts
import tsa

import numpy as np
from bokeh.plotting import figure, show, output_file, vplot
import pandas as pd
from bokeh.models.ranges import Range1d
from bokeh.io import save
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf  
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
from bokeh.io import gridplot, output_file, show
from bokeh.plotting import figure

import bokeh.plotting as bp
from bokeh.models import HoverTool 
from bokeh._legacy_charts import Bar, output_file, show
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)
features = [ {'filename': 'applications.csv', 'minimum_feature_contribution': 0.5, 'chart_types': ['stacked-bar'], 'analysis': [ 'tsa']},
             {'filename': 'protocols.csv', 'minimum_feature_contribution': 0.01, 'chart_types': ['stacked-bar'], 'analysis': [ 'tsa']},
             {'filename': 'packet_size_distribution.csv', 'minimum_feature_contribution': 0.0, 'chart_types': ['stacked-bar', 'heat-map'], 'analysis': [ 'tsa', 'other']}
           ]

#functions in the this modul
def _add_more_info_to_df(df, filename):
    #dataframe problably has a unnamed column, leftover from the mongodb cursor to csv file conversion
    #remove that columns
    if df.columns[0] == 'Unnamed: 0':
        #change the df into a new df without this column (df.drop for this unnamed column does not work)
        df = df[df.columns[1:]]

    #print the dataframe just to haev an idea of the shape and contents
    logger.info('shape for ' + filename + ' ' + str(df.shape))
    logger.info('head -> ')
    logger.info(df.head())

    logger.info('Adding year, half year and quarter information to the dataframe, would be used later during analysis...')

    q_list = []
    h_list = []
    y_list = []
    for d in df['Date']:
        t = time.strptime(d, "%Y-%m-%d")
        if t.tm_mon % 3:
            q = (t.tm_mon / 3) + 1
        else:
            q = (t.tm_mon / 3)         
        q_list.append(q)

        if t.tm_mon % 6:
            h = (t.tm_mon / 6) + 1
        else:
            h = (t.tm_mon / 6) 
        h_list.append(h)

        y_list.append(t.tm_year)

    df.insert(1, 'Year', y_list)
    df.insert(2, 'Half', h_list)
    df.insert(3, 'Quarter', q_list)

    logger.info('after adding more info, head ->')
    logger.info(df.head())

    return df

def _do_visualization_and_analysis(file_name, minimum_feature_contribution, chart_types, analysis_types):
    #first visualizations...

    #read the csv into a dataframe
    try:
        df = pd.read_csv(file_name)
    except Exception, e:
        logger.error('Exception: ' + str(e)) 
        return

    df = _add_more_info_to_df(df, file_name)
    
    #draw a statcked chart for features that contribute more than a set minimum
    if 'stacked-bar' in chart_types:
        charts.draw_stacked_chart(df, file_name, minimum_feature_contribution)

    #draw a heatmap for packet size distribution
    if 'heat-map' in chart_types:
        charts.draw_heat_map(df, file_name, minimum_feature_contribution)

    #begin with the analysis
    if 'tsa' in analysis_types:
        tsa.model_tsa(df, file_name, minimum_feature_contribution)


def visualize_data(config):
    for feature in features:
        _do_visualization_and_analysis(feature['filename'], feature['minimum_feature_contribution'], feature['chart_types'], feature['analysis'])

if __name__ == '__main__':
    #main program starts here.. 
    #get logger object, probably already created
    print 'in main program..'
    visualize_data({})