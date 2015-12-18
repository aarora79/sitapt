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
import bokeh.plotting as bp
from bokeh.models import HoverTool 
import pandas as pd
import numpy as np
from bokeh._legacy_charts import Bar, output_file, show
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

#global varialbes for this file
logger = sa_logger.init(globals.PACKAGE_NAME)
NUMBER_OF_COLUMNS_TO_SKIP = 6
NUMBER_OF_COMPONENTS_FOR_PCA = 10
NUMBER_OF_CLUSTERS = 4
OUTPUT_DIR_NAME = "output"

def _do_PCA_and_transform(X):
  logger.info('about to do PCA with number of components = %d' % NUMBER_OF_COMPONENTS_FOR_PCA)
  pca = PCA(n_components = NUMBER_OF_COMPONENTS_FOR_PCA)
  pca.fit(X)
  X_prime = pca.transform(X)
  return X_prime, pca

def model_kmeans(df, file_name, minimum_feature_contribution):

    logger.info('running KMeans clustering on data from ' + file_name)

    #first 4 columns are Date, Year, Half, Quarter, so skip those to get to the data
    df2 = df[df.columns[NUMBER_OF_COLUMNS_TO_SKIP:]]

    #convert to a matrix, each row of the matrix represents one year (for example in terms of % of protocols OR % of applications OR % of packet size distribution)
    X = df2.as_matrix()
    X_prime, pca = _do_PCA_and_transform(X)

    logger.info('pca.explained_variance_ratio_ ' + str(pca.explained_variance_ratio_))

    
    logger.info('pca.components_ ' + str(pca.components_))

    logger.info('about to run KMeans with clusters  = %d' % NUMBER_OF_CLUSTERS)
    kmeans = KMeans(n_clusters = NUMBER_OF_CLUSTERS, random_state = 0)
    kmeans.fit(X_prime)

    #now that the fit is done, get the centroids so that they can be plotted for visualization
    centroids = kmeans.cluster_centers_

    #labels (cluster identifiers given by kmeans)
    labels = kmeans.labels_

    #lets plot it against the first two dimensions as they represent the highest variance (remember X_prime is a PCA transformed matrix)
    plt.scatter(X_prime[:, 0], X_prime[:, 1], c = labels)

    plt.scatter(centroids[:, 0], centroids[:, 1], marker='x', s=150, linewidths=5, zorder=10)

    file_name_wo_extn = file_name[:-4]
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_kmeans_scatter_plot.png')
    plt.savefig(output_file_name)
    plt.close()
    ####tried visualizing this as a 3d scatter plot..makes it more unclear..2d is better so stick with that
    ####code kept here just for reference
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')

    # #ax.scatter(x, y, z, c='r', marker='o')
    # ax.scatter(X_prime[:, 0], X_prime[:, 1], X_prime[:, 2], c = labels)
    # ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2], marker='x', s=150, linewidths=5, zorder=10)

    # # ax.set_xlabel('X Label')
    # # ax.set_ylabel('Y Label')
    # # ax.set_zlabel('Z Label')

    # plt.show()
    # #rearrange the column list so that the label appears along with date etc
    col_list_w_clustering_info = list(df.columns)
    col_list_w_clustering_info.insert(NUMBER_OF_COLUMNS_TO_SKIP, 'cluster')

    #insert labels as the new field in the dataframe
    df['cluster'] = labels

    #now the dataframe also has the same labels, now create a new df with rearranged labels
    df2 = df[col_list_w_clustering_info]

    #write this frame to a csv
    output_file_name = os.path.join(os.path.sep, os.getcwd(), OUTPUT_DIR_NAME, file_name_wo_extn, file_name_wo_extn + '_with_clustering_info.csv')
    df2.to_csv(output_file_name, index = False)
    logger.info('finished kmeans clutering of %s' % file_name)
