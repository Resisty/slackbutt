#!/usr/bin/env python
""" Settings module for slackbot
"""

import yaml
from runbot import CONFIG
with open(CONFIG, 'r') as yml:
    CONFIG = yaml.load(yml.read(), Loader=yaml.FullLoader)

default_reply = "I'm sorry, Dave, I'm afraid I can't do that."

API_TOKEN = CONFIG['API_TOKEN']

PLUGINS = [
        'plugins',
        ]
