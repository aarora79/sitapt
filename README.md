## Study of Internet traffic to analyze and predict traffic (SITAPT)

![Alt text](http://full/path/to/img.jpg "Applications ordered by average percentage of packets contributed to total traffic from 2008 to 2015")

The last ten to fifteen years have seen a pervasive growth of the Internet both in terms of its depth of penetration into user population as well the breadth of areas into which Internet is now present. As Internet access becomes faster and applications move to the cloud the profile of Internet traffic continues to change. Peer to Peer traffic, video sharing and OTT (over the top) services coupled with almost ubiquitous access to high speed internet poses new challenges to service providers (how to better utilize bandwidth) as well OEMs (how to increase bits per second and packets per second through the equipment).

A key to understanding and solving these challenges is to understand what constitutes Internet traffic and how the internet traffic will look like in the coming years and then based on that optimize networks and infrastructure to better utilize available resources.  This is what this project aims to address i.e. understanding internet traffic from various perspectives (application, protocol, packet size and others) such that this understanding can then feed into network and infrastructure design. A data product named SITAPT (Study of Internet Traffic to Analyze and Predict Traffic) is built which addresses the aims of this project.

## Features

- Visualization of traffic data
- Time Series Analysis for Traffic Prediction
- Clustering to Explore Similarity
- Relationship between traffic types

## Installation and how to run

python setup.py install

To run the program, say

%run sitapt.py -c username:password -w 'sitapt.log' -d D:\\datalake -u https://data.caida.org/datasets/passive-2015/ https://data.caida.org/datasets/passive-2014/ https://data.caida.org/datasets/passive-2013/ https://data.caida.org/datasets/passive-2012/ https://data.caida.org/datasets/passive-2011/ https://data.caida.org/datasets/passive-2010/ https://data.caida.org/datasets/passive-2009/ https://data.caida.org/datasets/passive-2008/ -a "{"ingest" : { "make_list" : true, "download": true}, "wrangle":{"transform": true}, "analyze":{"create_analysis_db":true, "analyze": true},"visualize": {"visualize": true}}"

To selectively run portions of the pipeline only include those actions that you want executed. For example, to only run the visualization part, just say
%run sitapt.py -a visualize

the visualize part is probably the only part you want to run unless you want to download new data.

## License

Free software: ISC license




