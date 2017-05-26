#!/usr/bin/python
# =======================================
#
#  File Name : multco_bridges.py
#
#  Purpose :
#
#  Creation Date : 03-05-2015
#
#  Last Modified : Fri 26 May 2017 11:00:37 AM CDT
#
#  Created By : Brian Auron
#
# ========================================
import yaml
import json
import logging
import dateutil.parser as dateparser
import dateutil.tz as tz
import requests
requests.packages.urllib3.disable_warnings()
import os
import sseclient

#import slackbot.bot
import peewee
from playhouse.postgres_ext import PostgresqlExtDatabase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as fptr:
    cfg = yaml.load(fptr.read())
DBUSER = cfg['dbuser']
DBPASS = cfg['dbpass']
DB = cfg['db']
MULTCO_TOKEN = cfg['multco_token']
MULTCO_API = 'https://api.multco.us/bridges'

psql_db = PostgresqlExtDatabase(DB, user=DBUSER, password=DBPASS)

class PacificDate(object):
    @classmethod
    def from_str(cls, s):
        d = dateparser.parse(s).astimezone(tz.gettz('America/Los Angeles'))
        return d

class BridgeAPI(object):
    def __init__(self, token=MULTCO_TOKEN):
        self._token = token
        self._url = MULTCO_API
        self._uri = ''
        self._params = {'access_token': self._token}
        self._headers = {'Content-type': 'application/json'}
        self._bridges = None
        self._sse = None
    @property
    def params(self):
        return self._params
    @params.setter
    def params(self, p):
        self._params.update(p)
        return self._params
    @property
    def headers(self):
        return self._headers
    @headers.setter
    def headers(self, h):
        self._headers.update(h)
        return self._headers
    @property
    def sse(self):
        if not self._sse:
            self._sse = (sseclient
                         .SSEClient(self._url +
                                    '/sse?access_token={%s}' % self._token))
        while True:
            try:
                for msg in self._sse:
                    try:
                        data = json.loads(str(msg))
                        changed = data['changed']
                        bridge, item = changed['bridge'], changed['item']
                        if item != 'status':
                            raise KeyError('Uninterested in item that is not \
"status"')
                    except (ValueError, KeyError):
                        continue
                    if data[bridge][item]:
                        event_time = data[bridge]['upTime']
                        event = 'raised'
                    else:
                        event_time = data[bridge]['lastFive'][0]['downTime']
                        event = 'lowered'
                    event_time = PacificDate.from_str(event_time)
                    yield '%s bridge was %s at %s!' % (bridge.capitalize(),
                                                       event,
                                                       event_time)
            except (requests.exceptions.HTTPError,
                    requests.exceptions.ConnectionError,
                    KeyError) as err:
                logging.info(err)
                continue
    def _get(self):
        r = requests.get(url=self._url+self._uri,
                         headers=self._headers,
                         params=self._params)
        return r
    def _getjson(self):
        return self._get().json()

    @property
    def bridges(self):
        if not self._bridges:
            self._uri = ''
            self._bridges = self._getjson()
        return self._bridges

    def update_events(self):
        for bridge in self.bridges:
            self._uri = '/%s/events' % bridge['name']
            scheduled = self._getjson()['scheduledEvents']
            actual = self._getjson()['actualEvents']
            bridge['events'] = {'scheduled': sorted([PacificDate
                                                     .from_str(i['upTime'])
                                                     for i in scheduled]),
                                'actual': sorted([PacificDate
                                                  .from_str(i['upTime'])
                                                  for i in actual])}
        return self.bridges

    def pretty_events(self):
        bridges = self.update_events()
        s = ''
        for bridge in bridges:
            s += '%s scheduled events:\n' % bridge['name']
            if bridge['events']['scheduled']:
                s += ('\n'
                      .join(['- %s' % str(i)
                             for i in bridge['events']['scheduled']]))
            else:
                s += 'None\n'
        return s
