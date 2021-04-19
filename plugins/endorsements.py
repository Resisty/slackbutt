#!/usr/bin/python
""" Module for collecting and reporting on endorsements between slack users
"""
import functools
import re
import os
import collections
import logging
import peewee
import yaml
import slackbot.bot
from playhouse.postgres_ext import PostgresqlExtDatabase
# pylint: disable=protected-access

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as fptr:
    CFG = yaml.load(fptr.read(), Loader=yaml.FullLoader)
DBUSER = CFG['dbuser']
DBPASS = CFG['dbpass']
DB = CFG['db']
PSQL_DB = PostgresqlExtDatabase(DB, user=DBUSER, password=DBPASS)
LOGGER = logging.getLogger('slackbot.plugins.endorsements')

class EndorsementError(Exception):
    """ Custom error
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class EndorsementExistsError(Exception):
    """ Custom error when endorsement exists
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class BaseModel(peewee.Model):
    """ Super class for db models
    """
    class Meta:  # pylint: disable=too-few-public-methods
        """ Metaclsss for storing db connection
        """
        database = PSQL_DB

class Person(BaseModel):
    """ DB model for a slack user
    """
    slack_id = peewee.CharField(unique=True)

class Skill(BaseModel):
    """ DB model for an endorsement('s name)
    """
    key = peewee.TextField(unique=True)

class Endorsement(BaseModel):
    """ DB model for an endorsment from somebody to something else about something
    """
    endorser = peewee.ForeignKeyField(Person, related_name='endorser')
    endorsee = peewee.ForeignKeyField(Person, related_name='endorsee')
    skill = peewee.ForeignKeyField(Skill)

    class Meta:  # pylint: disable=too-few-public-methods
        """ Metaclass storing db connection and index for many-to-many relationships
        """
        indexes = (
            (('endorser', 'endorsee', 'skill'), True),
        )
        database = PSQL_DB

def connect(func):
    """ Decorator for connecting to database
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """ Wrapper function establishing db connection and running wrapped function
        """
        try:
            PSQL_DB.connect()
            return func(*args, **kwargs)
        finally:
            PSQL_DB.close()
    return wrapper

@connect
def create_tables():
    """ Create endorsements tables
    """
    PSQL_DB.create_tables([Person, Skill, Endorsement])

@connect
def drop_tables():
    """ Drop endorsements tables
    """
    PSQL_DB.connect()
    PSQL_DB.drop_tables([Person, Skill, Endorsement])

def user(msg):
    """ Get the user who sent a message
    """
    return msg._client.users[msg._get_user_id()]['name']

def users(msg):
    """ Get all slack users from message's client
    """
    return dict(msg._client.users.items())

@connect
def endorse(endorser_sid, endorsee_sid, skill):
    """ Create an endorsement in the db
    """
    try:
        _skill, _ = Skill.get_or_create(key=skill)
        _endorser, _ = Person.get_or_create(slack_id=endorser_sid)
        _endorsee, _ = Person.get_or_create(slack_id=endorsee_sid)
    except peewee.InternalError:
        raise EndorsementError('Something went wrong while trying endorse. Sorry! Try again!')
    try:
        endorsement = Endorsement.create(endorser=_endorser,
                                         endorsee=_endorsee,
                                         skill=_skill)
        return endorsement
    except peewee.IntegrityError:
        raise EndorsementExistsError('Cannot endorse twice!')

@connect
def get_endorsements(msg, slack_id=None):
    """ Get endorsements from the db, optionally for only a single user
    """
    query = (Endorsement
             .select(Endorsement.endorsee,
                     Endorsement.skill,
                     peewee.fn.COUNT(Endorsement.id)
                     .alias('count')))
    if slack_id:
        query = (query
                 .join(Person,
                       on=(Person.id == Endorsement.endorsee))
                 .where(Person.slack_id == slack_id))
    query = query.group_by(Endorsement.endorsee, Endorsement.skill)
    endorse_dict = (collections
                    .defaultdict(lambda: collections.defaultdict(dict)))
    slackers = users(msg)
    for endo in query:
        nick = slackers[endo.endorsee.slack_id]['name']
        endorse_dict[nick][endo.skill.key] = endo.count
    return endorse_dict

ENDORSE_STRING = r'''endorse\s<@([A-Z0-9]+)>(\sfor)?\s(.*)'''
ENDORSE = re.compile(ENDORSE_STRING, re.I|re.X)
@slackbot.bot.respond_to(ENDORSE)
def do_endorse(msg, *groups):
    '''@mention to endorse a user (by @mention) for something
Example: @bot endorse @user1234 for endorsements
Quoted endorsements are considered separate from unquoted'''
    LOGGER.info('Got an endorsement request')
    endorser = msg._get_user_id()
    endorsee = groups[0]
    skill = groups[2]
    try:
        _ = endorse(endorser, endorsee, skill)
    except (EndorsementError, EndorsementExistsError) as err:
        msg.reply(str(err))
        return
    endorser_nick = users(msg)[endorser]['name']
    endorsee_nick = users(msg)[endorsee]['name']
    reply = f'{endorser_nick} has endorsed {endorsee_nick} for "{skill}"'
    msg.reply(reply)

ENDORSE_LIST_STRING = r'''list\sendorsements((\sfor)?\s<@([A-Z0-9]+)>)?'''
ENDORSE_LIST = re.compile(ENDORSE_LIST_STRING, re.I|re.X)
@slackbot.bot.respond_to(ENDORSE_LIST)
def list_endorse(msg, *groups):
    '''@mention to list endorsements for a user
Example: @bot list endorsements for @user1234'''
    endorsements = get_endorsements(msg, groups[2])
    reply = '```\n'
    for slacker, endo_dict in endorsements.items():
        reply += 'Name: %s\n' % slacker
        for endorsement, count in endo_dict.items():
            reply += 'Endorsements for %s: %d\n' % (endorsement, count)
    reply += '```'
    sender = user(msg)
    (msg
     ._client
     .send_message('@%s' % sender,
                   reply))

VAX_STRING = r'''who\sis\svaccinated\??'''
VAX_PAT = re.compile(VAX_STRING, re.I|re.X)
@slackbot.bot.respond_to(VAX_PAT)
def list_vax(msg, *groups):
    '''@mention to list users who are vaccinated
Example: @bot who is vaccinated'''
    LOGGER.info('Got request to list "vaccinated" endorsements')
    vaxd_users = []
    user_endos = get_endorsements(msg)
    for nick, endos in user_endos.items():
        if 'vaccinated' in endos:
            vaxd_users.append(nick)
    reply = 'The following users have been endorsed for "vaccinated":\n```'
    reply += '\n'.join(vaxd_users)
    reply += '\n```'
    msg.reply(reply)



DEBUG = r'''.*'''
DEBUGGER = re.compile(DEBUG, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(DEBUGGER)
def debug(msg):
    """ Dump all requests to logger/stdout
    """
    LOGGER.info('DEBUG log - msg body: "%s"', msg.body)

