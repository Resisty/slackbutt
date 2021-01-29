#!/usr/bin/env python
""" Plugin module to transcribe Gregorian dates to Covid dates
"""

import re
import datetime

import dateparser
import slackbot.bot

EPOCH_YEAR = 2020
EPOCH_MONTH = 3
EPOCH_DAY = 12
EPOCH = datetime.datetime(EPOCH_YEAR, EPOCH_MONTH, EPOCH_DAY)

def to_covid(a_datetime):
    """ Convert a datetime object from Gregorian to Covid

        :param a_datetime: datetime.datetime object
        :return: A very stupid string that resembles a date
    """
    if a_datetime < EPOCH:
        diff = EPOCH - a_datetime
        diff_days = abs(0 - diff.days + 1)
        sign = '-' if diff_days > 0 else ''
    else:
        diff = a_datetime - EPOCH
        diff_days = EPOCH_DAY + diff.days
        sign = ''
    return (
        f'Gregorian {a_datetime.strftime("%F")} is Covid date {sign}{EPOCH_YEAR}-{EPOCH_MONTH}-'
        f'{diff_days}'
    )

DATESTRING = r'''[wW]hat day( of TYOOL 2020)? is (.*)\?'''
COVID_DATE = re.compile(DATESTRING, re.IGNORECASE)
@slackbot.bot.listen_to(COVID_DATE)
def covid_date(message, *groups):
    """ Listen for a question to the bot regarding date transcription from Gregorian to Covid

        :param message: The string message
        :param *groups: Iterable of re.search().groups()
    """
    the_date = dateparser.parse(groups[1])
    message.reply(to_covid(the_date))
