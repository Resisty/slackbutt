#!/usr/bin/python
# =======================================
#
#  File Name : github.py
#
#  Purpose :
#
#  Creation Date : 27-03-2016
#
#  Last Modified : Tue 17 Jan 2017 06:08:26 PM CST
#
#  Created By : Brian Auron
#
# ========================================

import os
import re
import pyowm
import yaml
import datetime
import slackbot.bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as yml:
    cfg = yaml.load(yml.read())
APIKEY = cfg['owm']['key']
NUM_WEATHERS = 3

class WeatherBot(object):
    def __init__(self, apikey=APIKEY):
        self._owm = pyowm.OWM(apikey)
        self._num = NUM_WEATHERS
    def weather_at(self, location, num=None):
        if num:
            self._num = num
        forecaster = (self
                    ._owm
                    .three_hours_forecast(location)
                    )
        forecast = forecaster.get_forecast()
        for weather in forecast.get_weathers()[:self._num]:
            yield weather
    @property
    def num(self):
        return self._num

WEATHERSTRING = r'''weather\s(.*)'''
WEATHER = re.compile(WEATHERSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(WEATHER)
def list_issues(message, *groups):
    location = groups[0]
    wbot = WeatherBot()
    msg = 'Next %s 3-hour weathers for %s\n' % (wbot.num, location)
    for weather in wbot.weather_at(location):
        msg += ('%s (%sF)\n'
                % (weather.get_detailed_status(),
                   weather.get_temperature('fahrenheit')['temp']))
    message.reply(msg)
    #print 'Got a message %s with groups "%s"' % (message.body, groups)
