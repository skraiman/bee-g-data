#!/usr/bin/python


from __future__ import print_function
import sys

import json
import time
from pprint import pprint
import geocoder
import sys, getopt
from urllib2 import quote
import os.path



try:
    from urllib.request import Request, urlopen  # Python 3
except:
    from urllib2 import Request, urlopen  # Python 2

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
#
# globals
#
configFile = os.path.expanduser('~/.beestuff')
#configFile = '/Users/skraimanarris/.beestuff'


def beekeepingIOGet(url, apikey):
    q = Request(url)
    q.add_header('license_key', apikey)
    data_file = urlopen(q)

    return json.load(data_file)

def getConfig():

    config = []

    if not os.path.isfile(configFile):
        config = {'startTime' : 0, 'stopTime' :  int(time.time()), 'geocodes': {}}
    else:
        with open(configFile) as data_file:
            config = json.load(data_file)
            config['startTime'] = config['stopTime'] + 1
            config['stopTime'] = int(time.time())
    return config


def putConfig(config):
    with open(configFile, 'w') as data_file:
        json.dump(config, data_file,  sort_keys=True,
            indent=4, separators=(',', ': '))


def getLocation(zipplus, config):
    if config['geocodes'].has_key(zipplus):
        print('cache hit for postal code ' + zipplus)
        g =  config['geocodes'][zipplus]
    else:
        print('cache miss for postal code ' + zipplus)
        g =  geocoder.arcgis(zipplus).json
        config['geocodes'][zipplus] = g

    return g

def processWeightsForPostalCode(postalCode, lat, lon, start, stop, apikey):

    pcLocation = { 'lat' : lat, 'lon' : lon}

    recs =[]
#    url = 'http://staging.beekeeping.io/api_v2/research/scales?' + 'postal_code=' + quote(postalCode) + \
#        '&start=' + str(start) + '&stop=' + str(stop)

    url = 'http://staging.beekeeping.io/api_v2/research/scales?postal_code=' + quote(postalCode) + \
        '&start=' + str(start) + '&stop=' + str(stop)

#    url = 'http://' + 'api.beekeeping.io/api_v2/research/weight?' + 'postal_code=' + quote(postalCode) + \
#        '&start=' + str(start) + '&stop=' + str(stop)

    eprint('url = ' + url)

    weights = beekeepingIOGet(url, apikey)


    if weights.has_key('payload'):
        for i in weights['payload']:
            weight = i['value']
            timestamp = i['timestamp']
            apiaryGUID = i['apiary_guid']
            deviceGUID = i['device_guid']
            hiveGUID = i['hive_guid']

            if i.has_key('latitude'):
                apiaryLocation = { 'lat' : i['latitude'], 'lon' : i['longitude']}

            recs.append({'timestamp': timestamp, 'postalCodeLocation': pcLocation, 'apiaryLocation' : apiaryLocation,
                'weight': float(weight), "postalCode" : postalCode,'apiaryGUID': apiaryGUID, 'deviceGUID': deviceGUID,
                'hiveGUID': hiveGUID})
    #        print i

    #eprint(recs)
    return recs



def outputJson(weights, outfile):
    if outfile == "":
        json.dump(weights, sys.stdout,  j=(',', ': '))
    else:
        with open(outfile, 'w') as data_file:
            json.dump(weights, data_file,  separators=(',', ': '))

def outputElastic(weights, outfile):
    index = 1

    if outfile == "":
        for rec in weights:
            print('{ "index" : { "_index" : "beez", "_type" : "weight"}')
    #        print('{ "index" : { "_index" : "beez", "_type" : "weight", "_id " : "', str(index), '" }}')
            print(json.dumps(rec))
            index = index + 1
    else:
        print("outfile is not blank")
        with open(outfile, 'w') as data_file:
            for rec in weights:
                data_file.write('{ "index" : { "_index" : "beez", "_type" : "weight"}\n')
#                data_file.write('{ "index" : { "_index" : "beez", "_type" : "weight", "_id" : "' + str(index) + '" }}\n')
                data_file.write(json.dumps(rec) + '\n')
                index = index + 1






def main(progname, argv):
    weights = []
    outfile = ""
    forElastic = False

    try:
        opts, args = getopt.getopt(argv,"ha:o:",["help","apikey=", "elastic", "outfile="])
    except getopt.GetoptError as err:
        eprint(str(err))
        usage(progname)
        sys.exit(2)
    for opt, arg in opts:
        eprint(opt, arg)
        if opt in ("-h", "--help"):
            usage(progname)
            sys.exit()
        elif opt in ("-a", "--apikey"):
            apikey=arg
        elif opt in ("-o", "--outfile"):
            outfile = arg
        elif opt in ("-o", "--elastic"):
            elastic = True


    print('elastic=', elastic)

    config = getConfig()

    start = config['startTime']
    stop = config['stopTime']
#    with open('/Users/skraimanarris/Documents/beekeeeping/zipcodes.json') as data_file:
#        data = json.load(data_file)

    url = 'http://api.beekeeping.io/api_v2/research/postal_codes'
    zips = beekeepingIOGet(url, apikey)

    for i in zips['payload']:
        postalCode = i['postal_code']
        zipplus =  postalCode + ', ' + i['country_code']
#    print zipplus
#        if postalCode == '18901':
        if True:
            g = getLocation(zipplus, config)
            if g['status'] == 'OK':
                lat = g['lat']
                lng = g['lng']
                #
                # add the latitude and longitude back to the origial record
                #
                i['lat'] = lat
                i['lng'] = lng

                try:
                    weights.extend(processWeightsForPostalCode(postalCode, lat, lng, start, stop, apikey))
                except ValueError as err:
                    eprint(str(err))
                #eprint("\n\n===============", weights, "\n\n\==================")
            else:
                eprint("postal code not found:" + postalCode)

    if elastic:
        outputElastic(weights, outfile)
    else:
        outputJson(weights,outfile)

    putConfig(config)
    exit(0)


def usage():
    eprint(progname + ' -t <token> [--outfile=oufile] [--elastic]!!!')



if __name__ == "__main__":
   main(sys.argv[0], sys.argv[1:])
