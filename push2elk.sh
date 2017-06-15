#!/bin/sh
#
# usage: push2elk.sh   elk-host   json-file-name
#
function chunkIt {

   TMPDIR="$(mktemp -d)"
   split -l 20000  $1  $TMPDIR/

   for f in $TMPDIR/*
   do
    echo "Processing $f"
    curl -XPOST "$HOST:9200/beez/_bulk?pretty" --data-binary @$f
   done

   rm -rf $TMPDIR
}
#
#
HOST=$1
echo "deleting old schema"
curl -XDELETE http://$HOST:9200/beez
echo "creating new schema"
curl -XPUT http://$HOST:9200/beez?pretty -d '
{
  "mappings": {
    "weight": {
      "properties": {
        "timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
        "postalCodeLocation": { "type": "geo_point" },
        "apiaryLocation": { "type": "geo_point" },
        "weight": {"type": "float"},
        "postalCode": {"type": "keyword"},
        "apiaryGUID": {"type": "keyword"},
        "hiveGUID": {"type": "keyword"},
        "deviceGUID": {"type": "keyword"}
      }
    },

    "temp": {
      "properties": {
        "timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
        "postalCodeLocation": { "type": "geo_point" },
        "postalCode": {"type": "keyword"},
        "temp": {"type": "float"}
      }
    }


  }
}
';
echo "printing out index info"
curl "$HOST:9200/_cat/indices?v"
echo "prining out mapping for beez"
curl "$HOST:9200/beez/_mapping/?pretty"
echo "loading data into elastic. . . ."
chunkIt $2
