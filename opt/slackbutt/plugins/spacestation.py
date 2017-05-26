
import re
import slackbot.bot
import requests
from datetime import datetime, timedelta

URL = 'http://api.open-notify.org/iss-pass.json?lat={0}&lon={1}'
LONGITUDE = -122.680372
LATITUDE = 45.522005

WHEREIS_URL = 'http://api.open-notify.org/iss-now.json'


class SpaceStation():
    def __init__(self, longitude=LONGITUDE, latitude=LATITUDE):
        self._longitude = longitude
        self._latitude = latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def latitude(self):
        return self._latitude

    @longitude.setter
    def longitude(self, longitude):
        self._longitude = longitude

    @latitude.setter
    def latitude(self, latitude):
        self._latitude = latitude

    def next_pass(self):
        reply = "nobody knows anything about a space station"
        url = URL.format(self._latitude, self._longitude)
        data = requests.get(url)
        if data.status_code == 200:
            api_response = data.json()
            if (api_response['message'] == 'success'):
                next_rise_time = api_response['response'][0]['risetime']
                next_duration = api_response['response'][0]['duration']
                dt = datetime.fromtimestamp(next_rise_time)
                done = dt + timedelta(seconds=next_duration)
                reply = "Next pass from {0} until {1}".format(
                    dt, done)
            else:
                print "had problem with api not success"

        else:
            print "status code for request '{0}' was {1}".format(
                url,
                data.status_code)
            api_response = data.json()
            if (api_response['message'] == 'failure'):
                reply = api_response['reason']
        return reply

    def current_location(self):
        reply = "nobody knows where it is"
        data = requests.get(WHEREIS_URL)
        if data.status_code == 200:
            api_response = data.json()
            if (api_response['message'] == 'success'):
                longitude = api_response['iss_position']['longitude']
                latitude = api_response['iss_position']['latitude']
                longstr = {True: "%s E", False: "%s W"}[longitude >= 0] % abs(
                    float(longitude))
                latstr = {True: "%s N", False: "%s W"}[latitude >= 0] % abs(
                    float(latitude))
                reply = "The ISS is at %s, %s" % (longstr, latstr)
        else:
            print "status code for current location request was {1}".format(
                data.status_code)
        return reply


ISS_STRING = r'''^iss[^\?$]?((-?[\d]+\.[\d]+)[,]?\s(-?[\d]+\.[\d]+))?'''
ISS = re.compile(ISS_STRING, re.IGNORECASE)


@slackbot.bot.respond_to(ISS)
def do_iss(message, *groups):
    '''@mention with a request for when the ISS will be at given coordinates
Examples: @bot iss iss -122.5, 45.4'''
    print "someone asked about the international space station!"
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
def do_where_is_iss(message, *groups):
    '''@mention the bot and ask about the ISS
Examples: @bot iss?
          @bot where is the iss?'''
    iss = SpaceStation()
    msg = iss.current_location()
    message.reply(msg)


if __name__ == '__main__':
    iss = SpaceStation(LONGITUDE, LATITUDE)
#    print iss.next_pass()
    print iss.current_location()
