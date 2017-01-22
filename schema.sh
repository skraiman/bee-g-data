#!/bin/sh
echo "deleting old schema"
curl -XDELETE http://localhost:9200/beez
echo "creating new schema"
curl -XPUT http://localhost:9200/beez?pretty -d '
{
  "mappings": {
    "weight": {
      "properties": {
        "timestamp": {"type": "date", "format": "YYYY-MM-DD HH:mm:ss"},
        "postalCodeLocation": { "type": "geo_point" },
        "apiaryLocation": { "type": "geo_point" },
        "weight": {"type": "float"},
        "postalCode": {"type": "keyword"},
        "apiaryGUID": {"type": "keyword"},
        "hiveGUID": {"type": "keyword"},
        "deviceGUID": {"type": "keyword"}
      }
    }
  }
}
';
echo "printing out index info"
curl 'localhost:9200/_cat/indices?v'
echo "prining out mapping for beez"
curl 'localhost:9200/beez/_mapping/weight?pretty'
echo "loading data into elastic. . . ."
#curl -XPOST 'localhost:9200/beez/_bulk?pretty' --data-binary @foobar.json
