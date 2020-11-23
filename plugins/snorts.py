#!/usr/bin/env python
""" Module for counting snorts
"""

import functools
import datetime
import re
import os
import operator
import yaml
import slackbot.bot
import peewee
from playhouse.postgres_ext import PostgresqlExtDatabase
from plugins import fakenumbers

# pylint: disable=protected-access

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, '../config.yml')
with open(CONFIG, 'r') as fptr:
    CFG = yaml.load(fptr.read(), Loader=yaml.FullLoader)
DBUSER = CFG['dbuser']
DBPASS = CFG['dbpass']
DB = CFG['db']
PSQL_DB = PostgresqlExtDatabase(DB, user=DBUSER, password=DBPASS)

def user(msg):
    """ Get user from slack message

        :param msg: Slack message
    """
    return msg._client.users[msg._get_user_id()]['name']

def users(msg):
    """ Get all users from slack message
        :param msg: Slack message
    """
    return [j['name'] for i, j in msg._client.users.items()]

class BaseModel(peewee.Model):
    """ Superclass allowing abstraction of database
    """
    class Meta:  # pylint: disable=too-few-public-methods
        """ Implementation class storing database connection
        """
        database = PSQL_DB


class Snorts(BaseModel):
    """ Class for storing who snorted when
    """
    nick = peewee.CharField()
    day = peewee.DateField()
    count = peewee.IntegerField(default=0)


class Counts(BaseModel):
    """ Class for storing a count of things and when
    """
    key = peewee.CharField(unique=True)
    count = peewee.IntegerField(default=0)
    day = peewee.DateField(null=True)


def connect(func):
    """ Database connection decorator
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """ Wrapper function that sets up the connection and executes the wrapped function
        """
        try:
            PSQL_DB.connect()
            return func(*args, **kwargs)
        finally:
            PSQL_DB.close()
    return wrapper

@connect
def create_tables():
    """ Create tables in DB
    """
    PSQL_DB.create_tables([Snorts, Counts])

@connect
def drop_tables():
    """ Drop tables in DB
    """
    PSQL_DB.connect()
    PSQL_DB.drop_tables([Snorts, Counts])

def do_snort(nick):
    """ Record a snort by a nickname

        :param nick: Nickname of the person who snorted
    """
    day = datetime.date.today()
    try:
        row = Snorts.select().where((Snorts.nick == nick) &
                                    (Snorts.day == day)).get()
    except peewee.DoesNotExist:
        row = Snorts.create(nick=nick, day=day)
    Snorts.update(count=Snorts.count + 1).where(Snorts.id == row.id).execute()
    row = Snorts.select().where(Snorts.id == row.id).get()
    return f'{row.nick} has snorted {row.count} snorts today.'

SNORTSTRING = r'''snort\s
                  ([\w-]+)'''
SNORT = re.compile(SNORTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(SNORT)
def snort_me(message, *groups):
    """ Record a snort for the user who sent the message
    """
    who = groups[0]
    if who == 'me':
        who = user(message)
    nicks = users(message)
    if who not in nicks:
        message.reply('Cannot snort %s a snort, nick not in channel.' % who)
    else:
        message.reply(do_snort(who))

SHOWSNORTSTRING = r'''show\ssnorts'''
SHOWSNORT = re.compile(SHOWSNORTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(SHOWSNORT)
def show_snorts(message):
    """ Detail all of the snorts from today
    """
    day = datetime.date.today()
    rows = Snorts.select().where(Snorts.day == day)
    results = []
    for row in rows:
        results.append(f'{row.nick} has snorted {row.count} snorts today.')
    if results == []:
        results.append('Nobody has snorted a snort today!')
    message.reply('\n'.join(results))

COUNTINGSTRING = r'''^([\w\.-]+)
                     (\+\+|--)$'''
COUNTING = re.compile(COUNTINGSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(COUNTING)
def count_update(message, *groups):
    """ Increment or decrement a count of something
    """
    key, delta = groups
    key = key.lower()
    delta = {'++': 1, '--': -1}[delta]
    try:
        truc = fakenumbers.NumberString.from_str(key)
        truc += delta
        message.reply(truc.str)
        return
    except fakenumbers.NoNumberError:
        pass
    with PSQL_DB.atomic():
        try:
            count = Counts.create(key=key, count=0)
        except peewee.IntegrityError:
            PSQL_DB.connect() # not entirely sure why this is necessary but it is
            count = Counts.get(Counts.key == key)
        count.count += delta
        count.save()
    message.reply(f'{key} is now {count.count}')

ARITHMETICSTRING = r'''^([\w\.-]+)\s
                     ([+\-\*/])=\s
                     (-?\d+)$'''
ARITHMETIC = re.compile(ARITHMETICSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(ARITHMETIC)
def arithmetic_update(message, *groups):
    '''Adjust a count arithmetically
Examples: a += 3
          counting -= 2
          stuff *= 0
          things /= 1'''
    key, oper, amount = groups
    key = key.lower()
    oper = {'+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.floordiv}[oper]
    with PSQL_DB.atomic():
        try:
            count = Counts.create(key=key, count=0)
        except peewee.IntegrityError:
            PSQL_DB.connect() # not entirely sure why this is necessary but it is
            count = Counts.get(Counts.key == key)
        try:
            count.count = oper(count.count, int(amount))
        except ZeroDivisionError:
            message.reply('You can\'t divide by zero, stupid!')
            return
        count.save()
    message.reply('%s is now %s' % (key, count.count))

DELCOUNTSTRING = r'''delete\s
                     (\w+)$'''
DELCOUNT = re.compile(DELCOUNTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(DELCOUNT)
def count_delete(message, *groups):
    """ Delete a count of something from the db
    """
    key = groups[0]
    key = key.lower()
    try:
        count = Counts.select().where(Counts.key == key, Counts.count == 0).get()
        count.delete_instance()
        msg = '%s has been deleted.' % key
    except peewee.DoesNotExist:
        msg = '%s does not exist in the Counts table or it does not have a \
count of 0!' % key
    message.reply(msg)

GETCOUNTSTRING = r'''print\s
                     (\w+)$'''
GETCOUNT = re.compile(GETCOUNTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(GETCOUNT)
def count_get(message, *groups):
    """ Get a count of something from the db
    """
    key = groups[0]
    key = key.lower()
    try:
        message.reply(str(Counts.get(Counts.key == key).count))
    except peewee.DoesNotExist:
        message.reply('None')

GETCOUNTS_STRING = r'''list\scounts'''
GETCOUNTS = re.compile(GETCOUNTS_STRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(GETCOUNTS)
def count_list(message):
    """ List things being counted
    """
    try:
        message.reply(', '.join([i.key for i in Counts.select()]))
    except peewee.DoesNotExist:
        message.reply('Could not find keys for counts!')
