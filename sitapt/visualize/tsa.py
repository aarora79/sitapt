from __future__ import print_function
import os
import sys
import time
import argparse
import pkg_resources  # part of setuptools
from collections import OrderedDict
import shutil
import copy

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

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

import statsmodels.api as sm
import pandas as pd

from statsmodels.graphics.api import qqplot
from statsmodels.tsa.stattools import acf  
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.seasonal import seasonal_decompose

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)
NUMBER_OF_MONTHS_TO_PREDICT_FOR = 12
PREDICTION_START_OFFSET = 72
OUTPUT_DIR_NAME = "output"
color_list = [ 'Pink', 'Red', 'Orange', 'Brown', 'Green', 'Cyan', 'Blue', 'Purple']

def _get_y_max(feature_val_max):

    if feature_val_max <= 1:
        y_max = 1
    elif feature_val_max <= 5:
        y_max = 5
    elif feature_val_max <= 10:
        y_max = 10
    else:
        y_max = 100
    return y_max

def _write_to_string(s, t):
    s += t + '\n'
    return s

def _draw_multiple_line_plot(filename, title, X, y, colors, legend, line_dash, line_width, x_axis_type, x_axis_label, y_axis_label, y_start=0, y_end=10, width=800, height=400):
    
    #output_file(filename, title=title)
    p1 = figure(x_axis_type = x_axis_type, plot_width=width, plot_height=height, y_range=(y_start, y_end))   

    for i in range(len(y)):
        p1.line(X[i], y[i], color=colors[i], legend=legend[i], line_dash=line_dash[i], line_width=line_width[i])
    #p1.multi_line(X, y, color=colors, legend=legend, line_dash=line_dash, line_width=line_width)
    # p1.multi_line(xs=X,
    #             ys=y,
    #             line_color=colors,
    #             line_width=5)
    p1.title = title
    #p1.grid.grid_line_color='Black'
    #p.ygrid[0].grid_line_alpha=0.5
    p1.legend.orientation = "bottom_left"
    p1.grid.grid_line_alpha=0.75
    p1.xaxis.axis_label = x_axis_label
    p1.yaxis.axis_label = y_axis_label
    p1.ygrid.band_fill_color="olive"
    p1.ygrid.band_fill_alpha = 0.25
    p1.ygrid.minor_grid_line_color = 'navy'
    p1.ygrid.minor_grid_line_alpha = 0.1

    save(vplot(p1), filename=filename, title=title)  

def _draw_decomposition_plot(filename, X, decomposition, legend, x_axis_type, x_axis_label, width=800, height=400):

    # create a new plot
    s1 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='observed')
    s1.line(X, decomposition.observed, color="navy", alpha=0.5)

    # create another one
    s2 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='trend')
    s2.line(X, decomposition.trend, color="navy", alpha=0.5)

    # create and another
    s3 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='residual')
    s3.line(X, decomposition.resid, color="navy", alpha=0.5)

    s4 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='seasonal')
    s4.line(X, decomposition.seasonal, color="navy", alpha=0.5)

    # put all the plots in a grid layout
    p = gridplot([[s1, s2], [s3, s4]])

    save(vplot(p), filename=filename, title='seasonal_decompose')  

def _create_grid_plot_of_trends(df, X, col_list, filename):

    width  = 600
    height = 400
        
    color_palette = [ 'Black', 'Red', 'Purple', 'Green', 'Brown', 'Yellow', 'Cyan', 'Blue', 'Orange', 'Pink']
    i = 0
    #2 columns, so number of rows is total /2 
    row_index = 0
    row_list = []
    row = []
    for col in col_list[1:]: #skip the date column
        # create a new plot
        s1 = figure(x_axis_type = 'datetime', width=width, plot_height=height, title=col + ' trend')
        #seasonal decompae to extract seasonal trends
        decomposition = seasonal_decompose(np.array(df[col]), model='additive', freq=15)  
        s1.line(X, decomposition.trend, color=color_palette[i % len(color_palette)], alpha=0.5, line_width=2)

        row.append(s1)
        if len(row) == 2:
            row_copy = copy.deepcopy(row)
            row_list.append(row_copy)
            row = []
            i = 0
        i += 1
        

    # put all the plots in a grid layout
    p = gridplot(row_list)

    save(vplot(p), filename=filename, title='trends')  

def _try_ARIMA_and_ARMA_models(s, df, feature):
    #model this as an ARIMA (Auto-Regressive Integrated Moving Average) with p=3, d=0, q=0
    #p is the number of autoregressive terms,
    #d is the number of nonseasonal differences needed for stationarity, and
    #q is the number of lagged forecast errors in the prediction equation.
    p_d_q_list = [ (1,0,0), (2,0,0), (3,0,0), (3,0,2), (2,0,2), (0,1,0), (0,0,1),
                   (1,1,0), (0,1,1), (1,1,1), (3,0,3), (1,0,6), (1,0,3)
                 ]
    #p,q list for ARMA
    p_q_list = [ (3,0), (2,0), (1,0), (2,1), (2,3) ]
    
    model_name_list = []
    model_list  = []
    result_list = []
    MAE_list    = []

    #first try ARIMA
    for p,d,q in p_d_q_list:
        try:
            model_name = "ARIMA_%d_%d_%d" % (p,d,q)
            
            model = sm.tsa.ARIMA(np.array(df[feature]), order=(p,d,q))  
            results = model.fit(disp=-1)  

            #calculate MAE (Mean absolute error) for finding out the effectiveness of the model
            y_actual = np.array(df[feature])
            y_fitted = results.fittedvalues
            MAE = np.mean(np.abs((y_actual - y_fitted) / y_actual)) * 100
            
            s = _write_to_string(s, '%s MAE: %s' % (model_name, str(MAE)))
            logger.info(model_name + ': ' + str(MAE))

            model_name_list.append(model_name)
            model_list.append(model)
            result_list.append(results)
            MAE_list.append(MAE)
        except Exception,e:
            logger.error(model_name + ' did not work for ' + feature)
            logger.error('Exception: ' + str(e))

    #now try ARMA
    for p,q in p_q_list:
        try:
            model_name = "ARMA_%d_%d" % (p,q)
            
            model = sm.tsa.ARMA(np.array(df[feature]), order=(p,q))  
            results = model.fit(disp=-1)  

            #calculate MAE (Mean absolute error) for finding out the effectiveness of the model
            y_actual = np.array(df[feature])
            y_fitted = results.fittedvalues
            MAE = np.mean(np.abs((y_actual - y_fitted) / y_actual)) * 100
            
            s = _write_to_string(s, '%s MAE: %s' % (model_name, str(MAE)))
            logger.info(model_name + ': ' + str(MAE))

            model_name_list.append(model_name)
            model_list.append(model)
            result_list.append(results)
            MAE_list.append(MAE)
        except Exception,e:
            logger.error(model_name + ' did not work for ' + feature)
            logger.error('Exception: ' + str(e))

    return s, model_name_list, model_list, result_list, MAE_list

def _do_forecasts(df, feature, X, s, model_names, models, results, MAE):

    #if no model was suitable then model_names and other lists would be empty
    if len(model_names) == 0:
        s += 'Did not find ANY suitable model for ' + feature
        logger.error('Did not find a suitable model for ' + feature + ', moving to the next feature.....')
        return s
    #the best model is the one with the minimum MAE..well thats what we are choosing to be the best anyway..
    index = MAE.index(min(MAE))
    logger.info('index = ' + str(index))
    msg = 'The best model for %s based on least MAE criterion is %s, it has an MAE of %f' % (feature, model_names[index], MAE[index])
    s = _write_to_string(s, msg)
    s = _write_to_string(s, 'Using %s for making predictions...' % (model_names[index]))
    logger.info('The best model for %s based on least MAE criterion is %s  ' % (feature, model_names[index]))
    logger.info('Using %s for making predictions...' % (model_names[index]))

    #now create a list for pointing out the selecting MAE mdoel, so all models would be marked as 0 except the selected one
    #which is marked as 1
    model_selection_list = [0] * len(MAE)
    #now mark the one which is selected as 1
    model_selection_list[index] = 1

    #logger.info ((np.mean((np.abs(df[feature].sub(results.fittedvalues).mean()) / results)))) # or percent error = * 100
    #predict next 10 values
    prediction_start_offset = PREDICTION_START_OFFSET
    num_predictions = NUMBER_OF_MONTHS_TO_PREDICT_FOR
    predicted_dates = []
    last_date = X[prediction_start_offset]
    for i in range(num_predictions):
        next_date = last_date + 30 # increment by one month, we want to predict on a month by month
        predicted_dates.append(next_date)
        last_date = next_date

    #predicted_dates=np.array(['2015-10-17', '2015-12-19', '2016-03-19', '2016-06-19', '2016-09-19'], dtype=np.datetime64)
    #print predicted_dates
    predicted = results[index].predict(start=prediction_start_offset, end=prediction_start_offset + num_predictions - 1)

    logger.info(predicted_dates)
    logger.info(predicted)
    s = _write_to_string(s, 'predicted_Dates ' + str(predicted_dates))
    s = _write_to_string(s, 'predicted_Values ' + str(predicted))

    #determine what would be a good y axis scale...most of the values are less than 10 so use a 1 to 10 scale or 1 to 100 otherwise
    y_max = _get_y_max(df[feature].max())

    _draw_multiple_line_plot('forecast.html', 
                             'transport layer protocols', 
                             [X,X, predicted_dates],
                             [np.array(df[feature]), results[index].fittedvalues, predicted],
                             ['navy', 'green', 'red'], 
                             ['observed packets percentage', 'fitted packets percentage', 'predicted'],
                             [None, None, None],
                             [1,1,1],
                             'datetime', 'Date', 'Packets Percentage', y_start=0, y_end=y_max)

    summary = results[index].summary()
    logger.info(summary)
    s = _write_to_string(s, str(summary))
    return s, predicted_dates, predicted, model_selection_list

def model_feature(file_name, df, feature):
    #first create a directory by feature name to store the results
    file_name_wo_extn = file_name[:-4]
    dir_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, feature)
    if os.path.exists(dir_name):
        logger.info('dir name is ==> ' + dir_name)
        #delete existing directory if any
        shutil.rmtree(dir_name)
    os.makedirs(dir_name)
    #temporarily change to the new feature directory
    curr_dir = os.getcwd()
    os.chdir(dir_name)

    #create  a string buffer to store all information about this feature which will then be written to a file at the end
    s = ''
    s = _write_to_string(s, '----------- Time Series Analysis for ' + feature + ' from ' + str(df['Date'][0]) + ' to ' + str(df['Date'][len(df['Date']) - 1]) + '-----------')
    #only look at the fearture of intrest as a univariate time series
    #x-axis is the time..
    X = np.array(df['Date'], dtype=np.datetime64)
    
    #df['First Difference'] = df[feature] - df[feature].shift()  
    y = np.array(df[feature] - df[feature].shift())
    _draw_multiple_line_plot('first_difference.html', 
                             feature, 
                             [X],
                             [y],
                             ['navy'], 
                             ['packets percentage delta'],
                             [None],
                             [1],
                             'datetime', 'Date', 'Packets Percentage Delta', y_start=-100, y_end=100)

    #calculate autocorelation and partial auto corelation for the first difference
    lag_correlations = acf(y[1:])  
    lag_partial_correlations = pacf(y[1:])  

    logger.info ('lag_correlations')
    logger.info(lag_correlations)

    s = _write_to_string(s, 'lag_correlations')
    s = _write_to_string(s, str(lag_correlations))

    y = lag_correlations
    _draw_multiple_line_plot('lag_correlations.html', 
                             'lag_correlations', 
                             [X],
                             [y],
                             ['navy'], 
                             ['lag_correlations'],
                             [None],
                             [1],
                             'datetime', 'Date', 'lag_correlations', y_start=-1, y_end=1)


    logger.info ('lag_partial_correlations')
    logger.info(lag_partial_correlations)
    s = _write_to_string(s, 'lag_partial_correlations')
    s = _write_to_string(s, str(lag_partial_correlations))

    y = lag_partial_correlations
    _draw_multiple_line_plot('lag_partial_correlations.html', 
                             'lag_partial_correlations', 
                             [X],
                             [y],
                             ['navy'], 
                             ['lag_partial_correlations'],
                             [None],
                             [1],
                             'datetime', 'Date', 'lag_partial_correlations', y_start=-1, y_end=1)

    #seasonal decompae to extract seasonal trends
    decomposition = seasonal_decompose(np.array(df[feature]), model='additive', freq=15)  
    _draw_decomposition_plot('decomposition.html', X, decomposition, 'seasonal decomposition', 'datetime', 'decomposition', width=600, height=400)


    #run various ARIMA models..and see which fits best...
    s, model_names, models, results, MAE = _try_ARIMA_and_ARMA_models(s, df, feature)

    #check if we got consistent output, all 4 variables returns by the prev function are
    # lists..they should be the same length
    len_list = [len(model_names), len(models), len(results), len(MAE)]
    if len(len_list) == len_list.count(len_list[0]):
        #looks consistent, all lengths are equal
        logger.info('_try_ARIMA_models output looks consistent, returns %d models ' % len(model_names))
    else:
        logger.info('_try_ARIMA_models output IS NOT consistent, returns %d model names ' % len(model_names))
        logger.info(len_list)
        logger.info('EXITING.....')
        sys.exit()

    s, predicted_dates, predicted, model_selection_list = _do_forecasts(df, feature, X, s, model_names, models, results, MAE)
    
    #write everything to file
    with open(feature + '.txt', "w") as text_file:
        text_file.write(s)
    #go back to parent directory
    os.chdir(curr_dir)

    #return the results
    return feature, model_names, models, results, MAE, predicted_dates, predicted, model_selection_list

def model_tsa(df, file_name, minimum_feature_contribution):
    #first get a list of features to model
    #each significant feature (protocol or application) would be modeled as an ARIMA (auto regressive moving average)
    #the modeling artifacts i.e. charts, sumary etc would be stored in a directory by feature name
    logger.info('Begin feature extraction...')
    col_list, remaining_features, remaining_features_values = va_utils.get_significant_features(df, minimum_feature_contribution)

    #store the results in a dataframe
    df_output = pd.DataFrame()
    feature_name_list = []
    model_name_list   = []
    MAE_list          = []
    model_selection_list = []
    
    predicted_col_list_with_data = ['Date'] + col_list
    df_predictions = pd.DataFrame(columns = predicted_col_list_with_data )
    logger.info('columns in oredicted df...')
    logger.info(predicted_col_list_with_data)
    df3 = df_predictions
    #df_w_predictions = copy.deepcopy(df[col_list])

    for col in col_list:
        logger.info('-------- modeling ' + col + '-------------')
        curr_dir = os.getcwd()
        try:
            feature, model_names, models, results, MAE, predicted_dates, predicted, model_selection = model_feature(file_name, df, col)
            feature_name_list += [feature]*len(model_names)
            model_name_list   += model_names
            MAE_list          += MAE
            model_selection_list += model_selection
            df_predictions['Date'] = predicted_dates
            df_predictions[feature] = predicted
        except Exception, e:
            logger.info('Could not model feature ' + col)
            logger.info('Exception: ' + str(e))
            os.chdir(curr_dir)

    #store the results in a dataframe and then write to a file
    df_output['feature'] = feature_name_list
    df_output['model']   = model_name_list
    df_output['MAE']     = MAE_list
    df_output['model_selected'] = model_selection_list
    file_name_wo_extn = file_name[:-4]
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_model_data.csv')
    df_output.to_csv(output_file_name, index = False)

    #create a grid plot of the trends in predicted protocols
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_trends.html')
    _create_grid_plot_of_trends(df, np.array(df['Date'], dtype=np.datetime64), predicted_col_list_with_data, output_file_name)
    #now create dataframe with predictions added
    #the date format in df_predictions is a string generated from np.datetime64 so it is of a different form
    #convert it to a string first
    df_predictions['Date'] = [str(d).split(' ')[0] for d in df_predictions['Date']]

    df_w_predictions = df[predicted_col_list_with_data].append(df_predictions)
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_with_forecasts.csv')
    df_w_predictions.to_csv(output_file_name, index = False)

    #draw a plot of all features including forecasted data..
    df_w_predictions = pd.read_csv(output_file_name)
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_with_forecasts.html')

    X = np.array(df_w_predictions['Date'], dtype=np.datetime64)
    colors_list_for_chart = []
    for i in range(len(col_list)):
        colors_list_for_chart.append(color_list[i % len(color_list)])

    matrix = []
    for col in col_list:
        matrix.append(np.array(df_w_predictions[col]))
    _draw_multiple_line_plot(output_file_name, 
                             file_name_wo_extn, 
                             [X] * len(col_list),  #col_list does not include the date column
                             matrix,
                             colors_list_for_chart, 
                             col_list,
                             [None] * len(col_list) ,
                             [1]  * len(col_list),
                             'datetime', 'Date', 'Packets Percentage', y_start=0, y_end=100)
    logger.info('finished feature modeling..')
