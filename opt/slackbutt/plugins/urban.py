#!/usr/bin/python
# =======================================
#
#  File Name :
#
#  Purpose :
#
#  Creation Date : 22-03-2016
#
#  Last Modified : Tue 22 Mar 2016 11:03:21 AM CDT
#
#  Created By : Brian Auron
#
# ========================================

import slackbot.bot
import re
import json
import random
import requests
import traceback

URBANSTRING = r'''urban\s([\w\s-]+)($|\s#\d+)'''
URBAN = re.compile(URBANSTRING, re.IGNORECASE)
@slackbot.bot.respond_to(URBAN)
def urban(message, *groups):
    try:
        what = groups[0]
        what = what.replace(' ', '%20')
        which = groups[1]
        if which:
            which = int(groups[1].strip().split('#')[1]) - 1
        else:
            which = 0
        url = 'http://api.urbandictionary.com/v0/define?term={0}'
        url = url.format(what)
        results = requests.get(url)
        jdata = json.loads(results.text)
        if jdata['result_type'] == 'no_results':
            msg = 'That\'s a stupid search!'
        else:
            try:
                msg = jdata['list'][which]['definition']
            except IndexError as e:
                msg = 'No such definition number!'
        message.reply(msg)
    except:
         print traceback.format_exc()
