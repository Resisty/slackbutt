# -*- coding: utf-8 -*-
#!/usr/bin/env python
""" Module for checking the weather somewhere
"""

import os
import re
import yaml
import pyowm
import slackbot.bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as yml:
    CFG = yaml.load(yml.read(), Loader=yaml.FullLoader)
APIKEY = CFG['owm']['key']
NUM_WEATHERS = 3

class WeatherBot:
    """ Class abstracting weather api
    """
    def __init__(self, apikey=APIKEY):
        self._owm = pyowm.OWM(apikey)
        self._num = NUM_WEATHERS
    def weather_at(self, location, num=None):
        """ Return the weather report (or a number of weather reports) at a location
        """
        if num:
            self._num = num
        forecaster = (
            self
            ._owm
            .three_hours_forecast(location)
        )
        forecast = forecaster.get_forecast()
        for weather in forecast.get_weathers()[:self._num]:
            yield weather
    @property
    def num(self):
        """ Propertize the number of weather reports to return
        """
        return self._num

WEATHERSTRING = r'''weather\s(.*)'''
WEATHER = re.compile(WEATHERSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(WEATHER)
def list_weathers(message, *groups):
    """ Respond to a request to list the next N weather reports in 3-hour blocks for a location
    """
    location = groups[0]
    wbot = WeatherBot()
    msg = f'Next {wbot.num} 3-hour weathers for {location}\n'
    for weather in wbot.weather_at(location):
        msg += (f"{weather.get_detailed_status()} ({weather.get_temperature('fahrenheit')['temp']}ºF)\n")
    message.reply(msg)
    #print(f'Got a message {message.body} with groups "{groups}"'
