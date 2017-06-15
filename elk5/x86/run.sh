#!/bin/sh
#
# store the elasticsearch data locally in ./elasticsearch-data so it persists across 
# the creation and destruction of the docker instances.
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker run --rm --name elastic -p 9200:9200  -v "$DIR/elasticsearch-data":/usr/share/elasticsearch/data -d  elasticsearch:5.1.2
docker run --rm --name kibana --link elastic:elasticsearch -p 5601:5601 -d kibana:5.1.2
#docker run --name elastic -p 9200:9200  -v "$DIR/elasticsearch-data":/usr/share/elasticsearch/data -d  elasticsearch:2.4
#docker run --name kibana --link elastic:elasticsearch -p 5601:5601 -d kibana:4.6
docker run --rm --name grafana --link elastic:elasticsearch  -d -p 3000:3000 -v "$DIR/grafana-data":/var/lib/grafana -e "GF_INSTALL_PLUGINS=mtanda-histogram-panel,grafana-piechart-panel,grafana-worldmap-panel,satellogic-3d-globe-panel" grafana/grafana
