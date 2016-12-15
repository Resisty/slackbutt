# -*- coding: utf-8 -*-
#!/usr/bin/python
# =======================================
#
#  File Name : plugins.py
#
#  Purpose :
#
#  Creation Date : 18-03-2016
#
#  Last Modified : Tue 12 Apr 2016 05:36:45 PM CDT
#
#  Created By : Brian Auron
#
# ========================================

import slackbot.bot
import re
import random
import traceback
import six

def user(msg):
    return msg._client.users[message._get_user_id()]['name']

SHENANISTRING = '''what's the name of that place you like with all the goofy\
 shit on the walls?'''
SHENANIGANS = [SHENANISTRING, re.IGNORECASE]
@slackbot.bot.respond_to(*SHENANIGANS)
def shenanigans(message):
    message.reply('You mean Shenanigans? You guys talkin\' \'bout\
 shenanigans?')

HI = re.compile(r'hi(|!)$', re.IGNORECASE)
@slackbot.bot.respond_to(HI)
def hi(message, groups):
    message.reply('Yo!')

TOWELSTRING = '''you're a towel'''
TOWEL = re.compile(TOWELSTRING, re.IGNORECASE)
@slackbot.bot.listen_to(TOWEL)
def towel(message):
    message.reply('''YOU'RE a towel!''')

PYTHONTOWELSTRING = '''you're a (bot|python|robot) towel'''
PYTHONTOWEL = re.compile(PYTHONTOWELSTRING, re.IGNORECASE)
@slackbot.bot.listen_to(PYTHONTOWEL)
def towel(message):
    message.reply('''What did you say?!''')

MARTINSTRING = '''martin'''
MARTIN = re.compile(MARTINSTRING, re.IGNORECASE)
@slackbot.bot.listen_to(MARTIN)
def martin(message):
    message.reply('''s/Martin/1950's newscast guy/g''')

GROUPSTRING = r'''^roll\sdice
                  $|\s
                  ((\s*[\d]+d[\d]+)+)
                  ($|\swith\s.*\smodifier(|s)\s((\s*[\+-]\d+)+))'''
GROUPS = re.compile(GROUPSTRING, re.IGNORECASE | re.VERBOSE)
@slackbot.bot.respond_to(GROUPS)
def roll_dice(message, *groups):
    try:
        dice = groups[0]
        try:
            modifiers = groups[4].split()
            modifiers = [int(m) for m in modifiers]
        except AttributeError as e:
            modifiers = [0]
        if not dice:
            total = random.randint(1,6)
            results = ['1d6: %d' % total]
        else:
            dice_sets = dice.split()
            total = 0
            results = []
            for dice_set in dice_sets:
                nums = dice_set.split('d')
                number = int(nums[0])
                size = int(nums[1])
                val = sum([random.randint(1, size) for i in range(number)])
                val += sum(modifiers)
                total += val
                results.append('%s: %d' % (dice_set, val))
        results = ', '.join(results)
        message.reply('''Got dice sets: %s\nTotal: %s''' % (results, total))
    except:
        print traceback.format_exc()

SPINSTRING = r'''spin\sthe\swheel'''
SPIN = re.compile(SPINSTRING, re.IGNORECASE | re.VERBOSE)
@slackbot.bot.respond_to(SPIN)
def spin_wheel(message):
    values = range(5, 105, 5)
    message.reply(str(random.choice(values)))

PINGSTRING = r'''^([^\w\s]*|_*)
                  ([a-zA-Z-_]+)
                  ING(S?)
                  ([^\w\s]*|_*)
                  (\sME(\s.*)?)?$'''
PING = re.compile(PINGSTRING, re.IGNORECASE | re.VERBOSE)
@slackbot.bot.listen_to(PING)
def ping(message, *groups):
    letter = groups[1]
    pre, suf = groups[0], groups[3]
    msg = 'ong' if letter[-1].islower() else 'ONG'
    msg += 's' if groups[2] and groups[2].islower() else 'S' if groups[2] else ''
    msg = pre+letter+msg+suf
    msg = 'Actually, it\'s "%s"' % msg
    message.reply(msg)

WHELPSTRING = '''whelps'''
WHELPS = re.compile(WHELPSTRING, re.IGNORECASE)
@slackbot.bot.listen_to(WHELPS)
def whelps(message):
    for i in ['WHELPS','LEFT SIDE','EVEN SIDE',
              'MANY WHELPS','NOW','HANDLE IT!']:
        message.reply(i)

FIXITSTRING = '''fixit'''
FIXIT = re.compile(FIXITSTRING, re.IGNORECASE)
@slackbot.bot.listen_to(FIXIT)
def fixit(message):
    message.reply('https://www.youtube.com/watch?v=8ZCysBT5Kec')

FINESTRING = '''this\sis\sfine'''
FINE = re.compile(FINESTRING, re.IGNORECASE)
@slackbot.bot.listen_to(FINE)
def this_is_fine(message):
    message.reply('http://gunshowcomic.com/648')

GREATDAYSTRING = r'''(it's\sgonna\sbe\sa\s)*
                    great\sday'''
GREATDAY = re.compile(GREATDAYSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(GREATDAY)
def great_day(message, *groups):
    message.reply('https://www.youtube.com/watch?v=WRu_-9MBpd4')

SPENDSTRING = r'''can\s
                     (.*)\s
                     spend\s
                     (this|that|the)\s
                     money'''
SPEND = re.compile(SPENDSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(SPEND)
def can_spend(message, *groups):
    message.reply('http://brianauron.info/CanBobiSpendThisMoney')

HADDAWAYSTRING = r'''(|,)\s
                     what\sis\slove\?*$'''
HADDAWAY = re.compile(HADDAWAYSTRING, re.IGNORECASE|re.VERBOSE)
@slackbot.bot.listen_to(HADDAWAY)
def what_is_love(message):
    message.reply('Baby don\'t hurt me!  https://www.youtube.com/watch?v=JRVfysTXhNA')

MANATEESTRING = '''[A-Z]{3}'''
MANATEE = re.compile(MANATEESTRING)
@slackbot.bot.listen_to(MANATEE)
def manatee_maybe(message):
    msg = message.body['text']
    nicks = [j['name'] for i,j in message._client.users.items()]
    if msg == msg.upper() and len(msg) > 4 and msg.lower() not in nicks:
        manatee = random.randint(1, 34)
        if manatee == 34:
            reply = 'https://cdn.meme.am/cache/instances/folder898/65169898.jpg'
        else:
            reply = 'http://calmingmanatee.com/img/manatee%s.jpg' % manatee
    else:
        return
    message.reply(reply)

PORTLANDSTRING = r'''tell\s(.+)\sto\scome\sto\sPortland'''
PORTLAND = re.compile(PORTLANDSTRING)
@slackbot.bot.respond_to(PORTLAND)
def come_to_portland(message, *groups):
    who = groups[0]
    message.send('@'+who+': http://i.imgur.com/29hMr0h.jpg')

SEATTLESTRING = r'''tell\s(.+)\sto\scome\sto\sSeattle'''
SEATTLE = re.compile(SEATTLESTRING)
@slackbot.bot.respond_to(SEATTLE)
def come_to_seattle(message, *groups):
    who = groups[0]
    message.send('@'+who+': http://i.imgur.com/Lwo0CTF.gif')

CLEVELANDSTRING = r'''tell\s(.+)\sto\scome\sto\sCleveland'''
CLEVELAND = re.compile(CLEVELANDSTRING)
@slackbot.bot.respond_to(CLEVELAND)
def come_to_cleveland(message, *groups):
    who = groups[0]
    message.send('@'+who+': https://www.youtube.com/watch?v=ysmLA5TqbIY')

ENHANCESTRING = r'''enhance'''
ENHANCE = re.compile(ENHANCESTRING)
@slackbot.bot.listen_to(ENHANCE)
def enhance(message):
    message.send('/me types furiously. "Enhance."')

@slackbot.bot.respond_to(re.compile('h[ae]lp', re.I))
def explore(message, *groups):
    udi = message._get_user_id()
    name = message._client.users[udi]['name']
    (message
     ._client
     .send_message('@%s' % name,
                   'Respond to:'))
    (message
     ._client
     .send_message('@%s' % name,
                   message.docs_reply()))
    (message
     ._client
     .send_message('@%s' % name,
                   'Listen to:'))
    reply = [u'    • `{0}` {1}'.format(v.__name__, v.__doc__ or '')
             for _, v in six.iteritems(message._plugins.commands['listen_to'])]
    (message
     ._client
     .send_message('@%s' % name,
                   u'\n'.join(reply)))
