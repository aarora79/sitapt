import os
import sys
import time
import argparse
import pkg_resources  # part of setuptools
from collections import OrderedDict
#import submodules
from globals import globals
from utils import sa_logger
import va_utils

import numpy as np
from bokeh.plotting import figure, show, output_file, vplot
import pandas as pd
from bokeh.models.ranges import Range1d
from bokeh.io import save
from bokeh.plotting import ColumnDataSource, figure, show, output_file

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
COLUMNS_TO_SKIP = 6
OUTPUT_DIR_NAME = 'output'

def draw_heat_map(df, file_name, minimum_feature_contribution):
    # this is the colormap from the original plot
    colors = [
        "#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce",
        "#ddb7b1", "#cc7878", "#933b41", "#550b1d"
    ]

    # Set up the data for plotting. We will need to have values for every
    # pair of year/month names. Map the rate to a color.
    interval = []
    date = []
    color = []
    value = []
    for d in df['Date']:
        for i in df.columns[COLUMNS_TO_SKIP:]:
            interval.append(i)
            date.append(d)
            percentage = float(df[df['Date'] == d][i])
            value.append(percentage)
            color_value = colors[int(percentage / len(colors))]
            color.append(color_value)

    source = ColumnDataSource(
        #data=dict(month=month, year=year, color=color, rate=rate)
        data=dict(interval=interval, date=date, color=color, value=value)
    )

    feature_name = file_name[:-4]
    #chart_file_name = feature_name + '_hm.html'
    file_name_wo_extn = file_name[:-4]
    chart_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn + '_hm.html')
    #output_file(chart_file_name)
    
    output_file(chart_file_name)

    TOOLS = "resize,hover,save,pan,box_zoom,wheel_zoom"
    title = feature_name.upper() + ' distribution from ' + str(df['Date'][0]) + ' to ' + str(df['Date'][len(df) - 1])
    
    p = figure(title=title,
        x_range= list(df['Date']), y_range=list(df.columns[COLUMNS_TO_SKIP:]),
        x_axis_location="above", plot_width=1300, plot_height=500,
        toolbar_location="left", tools=TOOLS)

    p.rect("date", "interval", 1, 1, source=source,
        color="color", line_color=None)

    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi/3

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ('date', '@date @interval'),
        ('percentage', '@value'),
    ])

    save(p)      # save the plt

def draw_stacked_chart(df, file_name, minimum_feature_contribution):
    logger.info('drawing stacked chart for ' + file_name)

    
    col_list, remaining_features, remaining_features_values = va_utils.get_significant_features(df, minimum_feature_contribution)   

    X = list(df['Date'])
    data = OrderedDict()
    for col in col_list:
        data[col] = df[col]
    #finally add the remaining features as a combined single column
    data['everything-else'] = remaining_features_values

    feature_name = file_name[:-4]
    #chart_file_name = feature_name + '.html'
    #output_file(chart_file_name)
    file_name_wo_extn = file_name[:-4]
    chart_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn + '_stacked_chart.html')
    output_file(chart_file_name)


    title = feature_name.upper() + ' distribution from ' + str(df['Date'][0]) + ' to ' + str(df['Date'][len(df) - 1])
    bar = Bar(data, X, title= title, stacked=True, legend='bottom_left', tools='hover,pan,wheel_zoom,box_zoom,reset,resize', width=1300, height=500)
    # glyph_renderers = bar.select(dict(type=GlyphRenderer))
    # bar_source = glyph_renderers[0].data_source

    # hover = bar.select(dict(type=HoverTool))
    # hover.tooltips = [
    #   ('name',' @cat'),
    #   ('number', '$y'),  
    # ]
    save(bar)
    logger.info('saved the chart in ' + chart_file_name)