#!/usr/bin/python
import functools
import yaml
import datetime
import re
import os
import collections
import slackbot.bot
import peewee
import fakenumbers
from playhouse.postgres_ext import PostgresqlExtDatabase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as fptr:
    cfg = yaml.load(fptr.read())
dbuser = cfg['dbuser']
dbpass = cfg['dbpass']
db = cfg['db']
psql_db = PostgresqlExtDatabase(db, user=dbuser, password=dbpass)

class EndorsementError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class EndorsementExistsError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class BaseModel(peewee.Model):
    class Meta:
        database = psql_db

class Person(BaseModel):
    slack_id = peewee.CharField(unique=True)

class Skill(BaseModel):
    key = peewee.TextField(unique=True)

class Endorsement(BaseModel):
    endorser = peewee.ForeignKeyField(Person, related_name='endorser')
    endorsee = peewee.ForeignKeyField(Person, related_name='endorsee')
    skill = peewee.ForeignKeyField(Skill)

    class Meta:
        indexes = (
                (('endorser', 'endorsee', 'skill'), True),
        )
        database = psql_db

def connect(func):
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    try:
      psql_db.connect()
      return func(*args, **kwargs)
    finally:
      psql_db.close()
  return wrapper

@connect
def create_tables():
    psql_db.create_tables([Person, Skill, Endorsement])

@connect
def drop_tables():
    psql_db.connect()
    psql_db.drop_tables([Person, Skill, Endorsement])

def user(msg):
    return msg._client.users[msg._get_user_id()]['name']

def users(msg):
    return {i:j for i, j in msg._client.users.items()}

def endorse(endorser_sid, endorsee_sid, skill):
    try:
        _skill, _ = Skill.get_or_create(key=skill)
        _endorser, _ = Person.get_or_create(slack_id=endorser_sid)
        _endorsee, _ = Person.get_or_create(slack_id=endorsee_sid)
    except peewee.InternalError:
        raise EndorsementError('Something went wrong while trying endorse. \
Sorry! Try again!')
    try:
        endorsement = Endorsement.create(endorser=_endorser,
                                         endorsee=_endorsee,
                                         skill=_skill)
        return endorsement
    except peewee.IntegrityError:
        raise EndorsementExistsError('Cannot endorse twice!')

def get_endorsements(msg, slack_id=None):
    q = (Endorsement
         .select(Endorsement.endorsee,
                 Endorsement.skill,
                 peewee.fn.COUNT(Endorsement.id)
                 .alias('count')))
    if slack_id:
        q = (q
             .join(Person,
                   on=(Person.id == Endorsement.endorsee))
             .where(Person.slack_id==slack_id))
    q = q.group_by(Endorsement.endorsee, Endorsement.skill)
    endorse_dict = (collections
                    .defaultdict(lambda : collections
                                          .defaultdict(dict)))
    slackers = users(msg)
    for endo in q:
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
    print 'Got an endorsement request'
    endorser = msg._get_user_id()
    endorsee = groups[0]
    skill = groups[2]
    try:
        endorsement = endorse(endorser, endorsee, skill)
    except (EndorsementError, EndorsementExistsError) as e:
        msg.reply(str(e))
        return
    endorser_nick = users(msg)[endorser]['name']
    endorsee_nick = users(msg)[endorsee]['name']
    reply = '%s has endorsed %s for "%s"' % (endorser_nick,
                                             endorsee_nick,
                                             skill)
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

DEBUG = r'''.*'''
DEBUGGER = re.compile(DEBUG, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(DEBUGGER)
def debug(msg):
    print msg.body
