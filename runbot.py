#!/usr/bin/env python
""" Script for running a slackbot
"""
import logging
import os
import slackbot.bot

logging.basicConfig()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, 'config.yml')
LOGGER = logging.getLogger('slackbot')
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

def main():
    """ Main function
    """
    bot = slackbot.bot.Bot()
    bot.run()

if __name__ == '__main__':
    main()
