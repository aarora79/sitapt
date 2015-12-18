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
import pandas as pd

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from scipy import stats
import matplotlib.pyplot as plt

import statsmodels.api as sm
from sklearn import linear_model

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)
OUTPUT_DIR_NAME = "output"

def do_linear_regression(file_name):
    try:
        logger.info('-------------------------------------')
        logger.info('TCP Vs UDP linear regression.........')
        logger.info('-------------------------------------')

        df = pd.read_csv(file_name)
        #plot TCP Vs UDP, so UDP goes on x axis
        x = np.array(df['UDP'])
        X = x[:, np.newaxis]
        y = np.array(df['TCP'])

        #create a linear regressor
        # Create linear regression object
        regr = linear_model.LinearRegression()

        # Train the model using the training sets
        regr.fit(X, y)

        # The coefficients
        logger.info('Coefficients: \n' + str(regr.coef_))
        # The mean square error
        logger.info("Residual sum of squares: %.2f"
              % np.mean((regr.predict(X) - y) ** 2))
        # Explained variance score: 1 is perfect prediction
        logger.info('Variance score: %.2f' % regr.score(X, y))

        # Plot outputs, just plot the regresion line through existing data
        fig = plt.figure()
        fig.suptitle('TCP Vs UDP, Linear Regression', fontsize=14, fontweight='bold')

        ax = fig.add_subplot(111)
        fig.subplots_adjust(top=0.85)
        
        ax.set_xlabel('UDP %')
        ax.set_ylabel('TCP %')

        plt.scatter(X, y,  color='black')
        plt.plot(X, regr.predict(X), color='blue',
                 linewidth=3)

        file_name_wo_extn = file_name[:-4]
        output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_tcp_vs_udp.png')
        plt.savefig(output_file_name)
        plt.close()
    except Exception,e:
        logger.error('Exception: ' + str(e))

     