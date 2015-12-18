===============================
sitapt
===============================

.. image:: https://img.shields.io/travis/aarora79/sitapt.svg
        :target: https://travis-ci.org/aarora79/sitapt

.. image:: https://img.shields.io/pypi/v/sitapt.svg
        :target: https://pypi.python.org/pypi/sitapt


Study of Internet traffic to analyze and predict traffic mix by protocol, application and other criteria (SITAPT)

* Free software: ISC license
* Documentation: https://sitapt.readthedocs.org.

Features
--------

* TODO
%run sitapt.py -c aa1603@georgetown.edu:amit1234 -w 'sitapt.log' -d D:\\datalake -u https://data.caida.org/datasets/passive-2015/ https://data.caida.org/datasets/passive-2014/ https://data.caida.org/datasets/passive-2013/ https://data.caida.org/datasets/passive-2012/ https://data.caida.org/datasets/passive-2011/ https://data.caida.org/datasets/passive-2010/ https://data.caida.org/datasets/passive-2009/ https://data.caida.org/datasets/passive-2008/ -a "{"ingest" : { "make_list" : true, "download": true}, "wrangle":{"transform": true}, "analyze":{"create_analysis_db":true, "analyze": true},"visualize": {"visualize": true}}"

