#!/usr/bin/python
# =======================================
#
#  File Name : runbot.py
#
#  Purpose :
#
#  Creation Date : 18-03-2016
#
#  Last Modified : Wed 07 Jun 2017 05:22:26 PM CDT
#
#  Created By : Brian Auron
#
# ========================================

import slackbot.bot
import logging
import threading
import time

import plugins.multco_bridges as mb

CONFIG = 'config.yml'
BRIDGE_CHANNEL = 'bridges'
BRIDGE_KILL_CHANNEL = 'general'
BRIDGE_VOMIT_SLEEP = 1800

def find_channel_by_name(client, channel_name):
    for channel_id, channel in client.channels.iteritems():
        try:
            name = channel['name']
        except KeyError:
            name = client.users[channel['user']]['name']
        if name == channel_name:
            return channel_id

def bridge_vomit(bot, bridgeapi):
    logging.info('Started bridge_vomit thread')
    while True:
        channel = find_channel_by_name(bot._client, BRIDGE_CHANNEL)
        if channel is None:
            channel = find_channel_by_name(bot._client, BRIDGE_KILL_CHANNEL)
            msg = 'I could not find the "bridges" channel. Bridges thread \
    shutting down.'
            bot._client.send_message(channel, msg)
            return
        for msg in bridgeapi.sse:
            if str(msg) != '':
                try:
                    bot._client.send_message(channel, msg)
                except HTTPError:
                    time.sleep(10) # Give slack a chance recover
                    continue

def botrun(bot):
    bot.run()

def main():
    bridgeapi = mb.BridgeAPI()
    logging.basicConfig()
    LOGGER = logging.getLogger('slackbot')
    bot = slackbot.bot.Bot()
    #bot.run()
    bot_thread = threading.Thread(target=botrun,
                                  args=[bot])
    bot_thread.start()
    bridge_thread = threading.Thread(target=bridge_vomit,
                                     args=[bot, bridgeapi])
    bridge_thread.start()

if __name__ == '__main__':
    main()
