import math
import random
import re

import requests
import slackbot.bot

GIPHY_API_KEY = 'dc6zaTOxFJmzC'
GIPHY_SEARCH_URL = 'http://api.giphy.com/v1/gifs/search'

@slackbot.bot.listen_to(re.compile('^giphy (.*)$', re.I))
def giphy(message, query):
    params = {'q': query, 'api_key': GIPHY_API_KEY}
    response = requests.get(GIPHY_SEARCH_URL, params=params)
    if not response.ok:
        message.reply('herp derp problems connecting to giphy API')
        return
    data = response.json()['data']
    if not data:
        message.reply('http://media2.giphy.com/media/rGcopDCOTAW8o/200.gif')
        return
    index = int(random.expovariate(math.sqrt(2)/2))
    if index >= len(data):
        index = 0
    message.reply(data[index]['images']['fixed_height']['url'])
