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
import datetime



#BEEKEEPING_IO=" https://beta.beekeeping.io"
#BEEKEEPING_IO=" http://app.beekeeping.io"
BEEKEEPING_IO=" https://app.beekeeping.io"
#BEEKEEPING_IO="http://staging.beekeeping.io"
#BEEKEEPING_IO="http://api.beekeeping.io"

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

def validate_date(date_text):
   try:
      datetime.datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
   except ValueError:
      raise ValueError("Incorrect data format, should be YYYY-MM-DD hh:mm:ss", date_text)


def beekeepingIOGet(url, apikey):

    eprint('url = ' + url)
    q = Request(url)
    q.add_header('license_key', apikey)
    data_file = urlopen(q)

    eprint("status code =", data_file.getcode(), " headers=", data_file.headers)

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


def processTempsForPostalCode(postalCode, lat, lon, start, stop, apikey):

    pcLocation = { 'lat' : lat, 'lon' : lon}

    recs =[]

    url = BEEKEEPING_IO + '/api_v2/research/temperature?postal_code=' + quote(postalCode) + \
        '&start=' + str(start) + '&stop=' + str(stop)

    temps = beekeepingIOGet(url, apikey)

    if temps.has_key('payload'):
        for i in temps['payload']:
            temp = i['value']
            timestamp = i['created']

            try:
                validate_date(timestamp)
            except ValueError:
                continue



            recs.append({'timestamp': timestamp, 'postalCodeLocation': pcLocation,
                'temp': float(temp), "postalCode" : postalCode})
    #        print i

    #eprint(recs)
    return recs






def processWeightsForPostalCode(postalCode, lat, lon, start, stop, apikey):

    pcLocation = { 'lat' : lat, 'lon' : lon}

    recs =[]
#    url = 'http://staging.beekeeping.io/api_v2/research/scales?' + 'postal_code=' + quote(postalCode) + \
#        '&start=' + str(start) + '&stop=' + str(stop)

    url = BEEKEEPING_IO + '/api_v2/research/scales?postal_code=' + quote(postalCode) + \
        '&start=' + str(start) + '&stop=' + str(stop)

#    url = 'http://' + 'api.beekeeping.io/api_v2/research/weight?' + 'postal_code=' + quote(postalCode) + \
#        '&start=' + str(start) + '&stop=' + str(stop)

#    eprint('url = ' + url)

    weights = beekeepingIOGet(url, apikey)


    if weights.has_key('payload'):
        for i in weights['payload']:
            weight = i['value']
            timestamp = i['timestamp']

            try:
                validate_date(timestamp)
            except ValueError:
                continue

            apiaryGUID = i['apiary_guid']
            deviceGUID = i['device_guid']
            hiveGUID = i['hive_guid']

            try:
                apiaryLocation = { 'lat' : float(i['latitude']), 'lon' : float(i['longitude'])}
                recs.append({'timestamp': timestamp, 'postalCodeLocation': pcLocation, 'apiaryLocation' : apiaryLocation,
                    'weight': float(weight), "postalCode" : postalCode,'apiaryGUID': apiaryGUID, 'deviceGUID': deviceGUID,
                    'hiveGUID': hiveGUID})
            except TypeError:
                recs.append({'timestamp': timestamp, 'postalCodeLocation': pcLocation,
                    'weight': float(weight), "postalCode" : postalCode,'apiaryGUID': apiaryGUID, 'deviceGUID': deviceGUID,
                    'hiveGUID': hiveGUID})
    #        print i

    #eprint(recs)
    return recs



def outputJson(weights,temps, outfile):
    stuff = weights
    stuff.append(temps)

    if outfile == "":
        json.dump(weights, sys.stdout,  j=(',', ': '))
    else:
        with open(outfile, 'w') as data_file:
            json.dump(weights, data_file,  separators=(',', ': '))

def outputElastic(weights, temps, outfile):
    index = 1

    if outfile == "":
        for rec in weights:
            print('{ "index" : { "_index" : "beez", "_type" : "weight"}}')
    #        print('{ "index" : { "_index" : "beez", "_type" : "weight", "_id " : "', str(index), '" }}')
            print(json.dumps(rec))
            index = index + 1
        for rec in temps:
            print('{ "index" : { "_index" : "beez", "_type" : "temp"}}')
    #        print('{ "index" : { "_index" : "beez", "_type" : "weight", "_id " : "', str(index), '" }}')
            print(json.dumps(rec))
            index = index + 1
    else:
        with open(outfile, 'w') as data_file:
            for rec in weights:
                data_file.write('{ "index" : { "_index" : "beez", "_type" : "weight"}}\n')
#                data_file.write('{ "index" : { "_index" : "beez", "_type" : "weight", "_id" : "' + str(index) + '" }}\n')
                data_file.write(json.dumps(rec) + '\n')
                index = index + 1

            for rec in temps:
                data_file.write('{ "index" : { "_index" : "beez", "_type" : "temp"}}\n')
        #                data_file.write('{ "index" : { "_index" : "beez", "_type" : "weight", "_id" : "' + str(index) + '" }}\n')
                data_file.write(json.dumps(rec) + '\n')
                index = index + 1






def main(progname, argv):
    weights = []
    temps = []
    outfile = ""
    elastic = False

    doWeight = False
    doTemp = False

    config = getConfig()

    start = config['startTime']
    stop = config['stopTime']

    try:
        opts, args = getopt.getopt(argv,"ha:o:",["help","apikey=", "elastic", "outfile=", "starttime=", "weight", "temp"])
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
        elif opt in ("-e", "--elastic"):
            elastic = True
        elif opt in ("--weight"):
            doWeight = True
        elif opt in ("-e", "--temp"):
            doTemp = True
        elif opt in ("--starttime"):
            start = int(arg)
        else:
            usage(progname)
            sys.exit()




    if len(argv) == 0:
        usage(progname)
        sys.exit(2)


    print('elastic=', elastic)
    print('start=', start)


#    with open('/Users/skraimanarris/Documents/beekeeeping/zipcodes.json') as data_file:
#        data = json.load(data_file)

    url = BEEKEEPING_IO + '/api_v2/research/postal_codes'
    zips = beekeepingIOGet(url, apikey)

    print(zips)

    for i in zips['payload']:
        postalCode = i['postal_code']
        zipplus =  postalCode + ', ' + i['country_code']
#    print zipplus
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
                if doWeight:
                    weights.extend(processWeightsForPostalCode(postalCode, lat, lng, start, stop, apikey))
                if doTemp:
                    temps.extend(processTempsForPostalCode(postalCode, lat, lng, start, stop, apikey))
            except ValueError as err:
                eprint(str(err))
            #eprint("\n\n===============", weights, "\n\n\==================")
        else:
            eprint("postal code not found:" + postalCode)

    if elastic:
        outputElastic(weights,temps,  outfile)
    else:
        outputJson(weights, temps, outfile)

    putConfig(config)
    exit(0)


def usage(progname):
    eprint(progname + ' --apikey=<token> [--outfile=oufile] [--starttime=<unixtimestamp>] [--elastic] [--weight] [--temp]\n\n')



if __name__ == "__main__":
   main(sys.argv[0], sys.argv[1:])
