#!/bin/sh
#
# store the elasticsearch data locally in ./elasticsearch-data so it persists across 
# the creation and destruction of the docker instances.
#
docker run --name elastic -p 9200:9200  -v "$PWD/elasticsearch-data":/usr/share/elasticsearch/data -d  elasticsearch:5.1.2
docker run --name kibana --link elastic:elasticsearch -p 5601:5601 -d kibana:5.1.2
