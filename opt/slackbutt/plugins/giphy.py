import math
import random
import re

import requests
import slackbot.bot

GIPHY_API_KEY = 'dc6zaTOxFJmzC'
GIPHY_SEARCH_URL = 'http://api.giphy.com/v1/gifs/search'

def get_gif(query):
    params = {'q': query, 'api_key': GIPHY_API_KEY}
    response = requests.get(GIPHY_SEARCH_URL, params=params)
    if not response.ok:
        return 'herp derp problems connecting to giphy API'
    data = response.json()['data']
    if not data:
        return 'http://media2.giphy.com/media/rGcopDCOTAW8o/200.gif'
    index = int(random.expovariate(math.sqrt(2)/2))
    if index >= len(data):
        index = 0
    return data[index]['images']['fixed_height']['url']

@slackbot.bot.listen_to(re.compile('^giphy (.*)$', re.I))
def giphy(message, query):
    '''Request a giphy search. Results are weighted for relevance.
Example: giphy your mom'''
    message.reply(get_gif(query))
