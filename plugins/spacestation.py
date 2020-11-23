#!/usr/bin/env python
""" Module for tracking the ISS
"""

import re
import logging
from datetime import datetime, timedelta
import slackbot.bot
import requests

URL = 'http://api.open-notify.org/iss-pass.json?lat={0}&lon={1}'
LONGITUDE = -122.680372
LATITUDE = 45.522005

WHEREIS_URL = 'http://api.open-notify.org/iss-now.json'
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler)


class SpaceStation():
    """ Class for using ISS api
    """
    def __init__(self, longitude=LONGITUDE, latitude=LATITUDE):
        self._longitude = longitude
        self._latitude = latitude

    @property
    def longitude(self):
        """ Propertize longitude
        """
        return self._longitude

    @property
    def latitude(self):
        """ Propertize latitude
        """
        return self._latitude

    @longitude.setter
    def longitude(self, longitude):
        self._longitude = longitude

    @latitude.setter
    def latitude(self, latitude):
        self._latitude = latitude

    def next_pass(self):
        """ Get next pass of ISS over location
        """
        reply = "nobody knows anything about a space station"
        url = URL.format(self._latitude, self._longitude)
        data = requests.get(url)
        if data.status_code == 200:
            api_response = data.json()
            if api_response['message'] == 'success':
                next_rise_time = api_response['response'][0]['risetime']
                next_duration = api_response['response'][0]['duration']
                nrt_datetime = datetime.fromtimestamp(next_rise_time)
                done = nrt_datetime + timedelta(seconds=next_duration)
                reply = f"Next pass from {nrt_datetime} until {done}"
            else:
                LOGGER.info("had problem with api not success")

        else:
            LOGGER.info("status code for request '%s' was %s", url, data.status_code)
            api_response = data.json()
            if api_response['message'] == 'failure':
                reply = api_response['reason']
        return reply

    @staticmethod
    def current_location():
        """ Get current location of ISS
        """
        reply = "nobody knows where it is"
        data = requests.get(WHEREIS_URL)
        if data.status_code == 200:
            api_response = data.json()
            if api_response['message'] == 'success':
                longitude = api_response['iss_position']['longitude']
                latitude = api_response['iss_position']['latitude']
                longstr = f"{abs(float(longitude))} {'E' if longitude >= 0 else 'W'}"
                latstr = f"{abs(float(latitude))} {'N' if latitude >= 0 else 'S'}"
                reply = f"The ISS is at {longstr}, {latstr}"
        else:
            LOGGER.info("status code for current location request was %s", data.status_code)
        return reply


ISS_STRING = r'''^iss[^\?$]?((-?[\d]+\.[\d]+)[,]?\s(-?[\d]+\.[\d]+))?'''
ISS = re.compile(ISS_STRING, re.IGNORECASE)


@slackbot.bot.respond_to(ISS)
def do_iss(message, *groups):
    '''@mention with a request for when the ISS will be at given coordinates
Examples: @bot iss iss -122.5, 45.4'''
    LOGGER.info("someone asked about the international space station!")
    try:
        longitude, latitude = groups[1], groups[2]
    except IndexError:
        longitude, latitude = LONGITUDE, LATITUDE  # constants for pdx
    iss = SpaceStation(longitude, latitude)
    msg = iss.next_pass()
    message.reply(msg)


WHEREIS_STRING = r'''iss\?$'''
WHEREIS = re.compile(WHEREIS_STRING, re.IGNORECASE)


@slackbot.bot.respond_to(WHEREIS)
def do_where_is_iss(message, *groups):  # pylint: disable=unused-argument
    '''@mention the bot and ask about the ISS
Examples: @bot iss?
          @bot where is the iss?'''
    iss = SpaceStation()
    msg = iss.current_location()
    message.reply(msg)


if __name__ == '__main__':
    ISS = SpaceStation(LONGITUDE, LATITUDE)
    LOGGER.info(ISS.current_location())
