#!/usr/bin/env python
""" Module for using the Multnomah bridge api
"""
import json
import logging
import os
import dateutil.parser as dateparser
import dateutil.tz as tz
import requests
import sseclient
import yaml
from playhouse.postgres_ext import PostgresqlExtDatabase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as fptr:
    CFG = yaml.load(fptr.read(), Loader=yaml.FullLoader)
DBUSER = CFG['dbuser']
DBPASS = CFG['dbpass']
DB = CFG['db']
MULTCO_TOKEN = CFG['multco_token']
MULTCO_API = 'https://api.multco.us/bridges'

PSQL_DB = PostgresqlExtDatabase(DB, user=DBUSER, password=DBPASS)

class PacificDate:  # pylint: disable=too-few-public-methods
    """ Class for ensuring datetimes are in Pacific tz
    """
    @classmethod
    def from_str(cls, datestring):
        """ Create a Pacific datetime from a string
        """
        date = dateparser.parse(datestring).astimezone(tz.gettz('America/Los Angeles'))
        return date

class BridgeAPI:
    """ Class for abstracting the Multnomah bridge api
    """
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
        """ Propertize api request params
        """
        return self._params
    @params.setter
    def params(self, prms):
        """ Override the api request params
        """
        self._params.update(prms)
        return self._params
    @property
    def headers(self):
        """ Propertize the request headers
        """
        return self._headers
    @headers.setter
    def headers(self, hdrs):
        """ Override the request headers
        """
        self._headers.update(hdrs)
        return self._headers
    @property
    def sse(self):
        """ Propertize the SSE client and its operation
        """
        if not self._sse:
            self._sse = (sseclient
                         .SSEClient(self._url +
                                    '/sse?access_token={'+self._token+'}'))
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
        req = requests.get(url=self._url+self._uri,
                           headers=self._headers,
                           params=self._params)
        return req
    def _getjson(self):
        return self._get().json()

    @property
    def bridges(self):
        """ Propertize bridges
        """
        if not self._bridges:
            self._uri = ''
            self._bridges = self._getjson()
        return self._bridges

    def update_events(self):
        """ Update bridge events from api
        """
        for bridge in self.bridges:
            self._uri = f"/{bridge['name']}/events"
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
        """ Create a pretty string for bridge information (for humans)
        """
        bridges = self.update_events()
        bridge_string = ''
        for bridge in bridges:
            bridge_string += f"{bridge['name']} scheduled events:\n"
            if bridge['events']['scheduled']:
                bridge_string += ('\n'.join([f'- {str(i)}' for i in bridge['events']['scheduled']]))
            else:
                bridge_string += 'None\n'
        return bridge_string
