#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PollAndPushServer.py: Script for query production values from Enphase-S gateway hosted
on a local server server and push data on InfluxDb.."""

__author__ = "César Papilloud, Pierre-A. Mudry"
__copyright__ = "Copyright 2018, FireMON, WaterMON, EarthMON, SpaceMON"
__version__ = "1.1.0"

import json
import urllib3
from influxdb import InfluxDBClient
import time
import progressbar
import argparse

# Sleep time setting
__sleepTime__ = 30
# InfluxDB settings
__host__ = 'localhost'
__port__ = 8086
__user__ = 'admin'
__password__ = 'admin'
__dbname__ = 'enphase'

# Getting arguments
parser = argparse.ArgumentParser()
parser.add_argument('--url', default="http://envoy.ayent/production.json",
        help='the URL of production.json (default: http://envoy.ayent/production.json)')

args = parser.parse_args()
__url__ = args.url

# Last reading time, used to avoid pushing same values twice
lastProductionInverterTime = 0
lastProductionEimTime = 0
lastConsumptionTime = 0
lastNetConsumptionTime = 0

"""Functions definitions"""
def pushData(data, seriesName, client):
        """Push data  into InfluxDB"""
        valQuery = [1]
        val = {}
        val["fields"] = data
        val["measurement"] = seriesName
        valQuery[0] = val
        client.write_points(valQuery)

client = InfluxDBClient(__host__, __port__, database=__dbname__)

"""Part 1 : Query production data from an url"""
print("************************")
print("Getting Enphase JSON information from server " + __url__)
# Query the url
try:
        import urllib.request
        with urllib.request.urlopen(__url__) as url:
            s = url.read()
#        response = urllib.urlopen(__url__)

        # Load response into json object
        data = json.loads(s)
        productionInverterData = data['production'][0]
        productionEimData = data['production'][1]
        consumptionData = data['consumption'][0]
        netconsumptionData = data['consumption'][1]

        """Part 2 : Check if readingTime is different"""
        print("************************")
        print("Time data from general information : ", productionInverterData['readingTime'])
        print("Time data from general data EIM : ", productionEimData['readingTime'])
        print("Time data from consumption : ", consumptionData['readingTime'])
        print("Time data from net consumption : ", netconsumptionData['readingTime'])
        print("************************")

        """Part 3 : Push data into InfluxDB, only if time is different"""
        if productionInverterData['readingTime'] > lastProductionInverterTime:
                print("Pushing production data")
                pushData(productionInverterData, "general_info", client)
                lastProductionInverterTime = productionInverterData['readingTime']

        if productionEimData['readingTime'] > lastProductionEimTime:
                print("Pushing general info")
                pushData(productionEimData, "production", client)
                lastProductionEimTime = productionEimData['readingTime']

        if consumptionData['readingTime'] > lastConsumptionTime:
                print("Pushing total consumption data")
                pushData(consumptionData, "total_consumption", client)
                lastConsumptionTime = consumptionData['readingTime']

        if netconsumptionData['readingTime'] > lastNetConsumptionTime:
                print("Pushing net consumption")
                pushData(netconsumptionData, "net_consumption", client)
                lastNetConsumptionTime = netconsumptionData['readingTime']

except Exception as e:
        print(e)

print("************************")

