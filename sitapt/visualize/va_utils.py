import os
import sys
import time
import argparse
import pkg_resources  # part of setuptools
from collections import OrderedDict
#import submodules
from globals import globals
from utils import sa_logger

COLUMNS_TO_SKIP = 4 #skip Date, Year, Half, Quarter
logger = sa_logger.init(globals.PACKAGE_NAME)

def get_significant_features(df, minimum_feature_contribution):

    #only consider a significant subset of the data
    col_list = []
    s = 0.0
    for col in df.columns[COLUMNS_TO_SKIP:]:
        #select columns for which the mean >= MINIMUM_FEATURE_CONTRIBUTION_PERCENTAGE
        m = df[col].mean()
        if m >= minimum_feature_contribution:
            print col + ' ' + str(m)
            col_list.append(col)
            s += m
    logger.info(str(len(col_list)) + ' features out of a total of ' + str(len(df.columns[COLUMNS_TO_SKIP:])) + ' features with % greater than ' + str(minimum_feature_contribution) + ' make up ' + str(s) + '% of the traffic..')
   

    remaining_features = [c for c in df.columns[COLUMNS_TO_SKIP:] if c not in col_list]
    remaining_features_values = []
    for i in range(len(df)):
        val = sum(df.loc[i, remaining_features])
        remaining_features_values.append(val)

    logger.info('remaining feature list ->')
    logger.info(remaining_features)

    return col_list,remaining_features,remaining_features_values