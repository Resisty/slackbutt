#!/usr/bin/python
# =======================================
#
#  File Name : snorts.py
#
#  Purpose :
#
#  Creation Date : 03-05-2015
#
#  Last Modified : Sat 29 Jul 2017 02:23:54 PM CDT
#
#  Created By : Brian Auron
#
# ========================================

import functools
import yaml
import datetime
import operator
import slackbot.bot
import peewee
import re
import os
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

def user(msg):
    return msg._client.users[message._get_user_id()]['name']

def users(msg):
    return [j['name'] for i,j in message._client.users.items()]

class BaseModel(peewee.Model):
    class Meta:
        database = psql_db


class Snorts(BaseModel):
    nick = peewee.CharField()
    day = peewee.DateField()
    count = peewee.IntegerField(default=0)


class Counts(BaseModel):
    key = peewee.CharField(unique=True)
    count = peewee.IntegerField(default=0)
    day = peewee.DateField(null=True)


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
    psql_db.create_tables([Snorts, Counts])

@connect
def drop_tables():
    psql_db.connect()
    psql_db.drop_tables([Snorts, Counts])

def do_snort(nick):
    day = datetime.date.today()
    try:
        row = Snorts.select().where((Snorts.nick == nick) &
                                    (Snorts.day == day)).get()
    except peewee.DoesNotExist as e:
        row = Snorts.create(nick = nick, day = day)
    Snorts.update(count = Snorts.count + 1).where(Snorts.id == row.id).execute()
    row = Snorts.select().where(Snorts.id == row.id).get()
    return '%s has snorted %s snorts today.' % (row.nick, row.count)

SNORTSTRING = r'''snort\s
                  ([\w-]+)'''
SNORT = re.compile(SNORTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(SNORT)
def snort_me(message, *groups):
    '''@mention with a request to add a snort for a user
Examples: @bot snort me
          @bot snort user1234'''
    who = groups[0]
    if who == 'me':
        who = user(message)
    nicks = users(message)
    if who not in nicks:
        message.reply('Cannot snort %s a snort, nick not in channel.' % who)
    else:
        message.reply(do_snort(who))
    data['reply'] = 'public'
    return data

SHOWSNORTSTRING = r'''show\ssnorts'''
SHOWSNORT = re.compile(SHOWSNORTSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.respond_to(SHOWSNORT)
def show_snorts(message):
    '''@mention with a request to show snorts
Example: @bot show snorts'''
    day = datetime.date.today()
    rows = Snorts.select().where(Snorts.day == day)
    results = []
    for row in rows:
        results.append('%s has snorted %s snorts today.' % (row.nick, row.count))
    if results == []:
        results.append('Nobody has snorted a snort today!')
    message.reply('\n'.join(results))

COUNTINGSTRING = r'''^([\w\.-]+)
                     (\+\+|--)$'''
COUNTING = re.compile(COUNTINGSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(COUNTING)
def count_update(message, *groups):
    '''Increment or decrement something
Examples: a++
          counting--'''
    key, delta = groups
    key = key.lower()
    delta = {'++': 1, '--': -1}[delta]
    try:
        s = fakenumbers.NumberString.from_str(key)
        s += delta
        message.reply(s.str)
        return
    except fakenumbers.NoNumberError:
        pass
    with psql_db.atomic():
        try:
            count = Counts.create(key = key, count = 0)
        except peewee.IntegrityError:
            psql_db.connect() # not entirely sure why this is necessary but it is
            count = Counts.get(Counts.key == key)
        count.count += delta
        count.save()
    message.reply('%s is now %s' % (key, count.count))

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
    key, oper, amount  = groups
    key = key.lower()
    oper = {'+': operator.add,
             '-': operator.sub,
             '*': operator.mul,
             '/': operator.floordiv}[oper]
    with psql_db.atomic():
        try:
            count = Counts.create(key = key, count = 0)
        except peewee.IntegrityError:
            psql_db.connect() # not entirely sure why this is necessary but it is
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
    '''@mention with a request to delete a counter. Counter's value \
must be 0.
Example: @bot delete counting'''
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
    '''@mention with a request to print a counter by name.
Example: @bot print counting'''
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
    '''@mention with a request to list counters.
Example: @bot list counts'''
    try:
        message.reply(', '.join([i.key for i in Counts.select()]))
    except peewee.DoesNotExist:
        message.reply('Could not find keys for counts!')
