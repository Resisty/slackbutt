#!/usr/bin/env python
""" Module for interacting with github; allow users to request/refer to issues for the bot
"""

import json
import os
import re
import requests
import yaml
import slackbot.bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as yml:
    CFG = yaml.load(yml.read(), Loader=yaml.FullLoader)

URL = CFG['github']['url']
OWNER = CFG['github']['owner']
REPO = CFG['github']['repo']
TOKEN = CFG['github']['token']
HEADERS = {'Content-Type': 'application/json',
           'Authorization': 'token %s' % TOKEN}

class Issue:
    """ Abstraction of a github issue
    """
    def __init__(self):
        self.uri = URL+f'/repos/{OWNER}/{REPO}/issues'
    def list(self, params=None):
        """ List all github issues for configured account+repo
        """
        if params is None:
            params = {}
        req = requests.get(self.uri, headers=HEADERS, params=params)
        return json.loads(req.text)
    def create(self, title, body):
        """ Create a github issue for the configured account+repo
        """
        data = {'title': title, 'body': body}
        req = requests.post(self.uri, headers=HEADERS, data=json.dumps(data))
        return json.loads(req.text)


LISTISSUESTRING = r'''github\slist\sissues?
                      ($|\sopen|\sclosed)?
                      ($|\sexpanded)'''
LISTISSUES = re.compile(LISTISSUESTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(LISTISSUES)
def list_issues(message, *groups):
    """ Reply to a request to list all github issues
    """
    param = groups[0]
    expanded = groups[1]
    params = {}
    if param:
        params['state'] = param
    resp = Issue().list(params=params)
    if len(resp) == 0:
        message.reply('0 issues found.')
        return
    if expanded:
        for i in resp:
            message.reply(f"Issue: {i['html_url']}\nTitle: {i['title']}\nDescription: {i['body']}")
    else:
        _ = [message.reply(i['html_url']) for i in resp]
    #print(f"Got a message {message.body} with groups '{groups}'")

CREATEISSUESTRING = r'''github\screate\sissue\s
                        ((title\s)?(".*"))\s
                        ((body\s)?(".*"))$'''
CREATEISSUE = re.compile(CREATEISSUESTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(CREATEISSUE)
def create_issue(message, *groups):
    """ Respond to a request to create a github issue for a user
    """
    title = groups[2].strip('"')
    body = groups[5].strip('"')
    resp = Issue().create(title, body)
    message.reply(resp['html_url'])
    #print(f'Got a message {message.body} with groups "{groups}"'
