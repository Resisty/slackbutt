#!/usr/bin/env python
""" Plugin module to transcribe Gregorian dates to Covid dates
"""

import re
import datetime
import logging

from dateutil import parser
import slackbot.bot

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())

EPOCH_YEAR = 2020
EPOCH_MONTH = 3
EPOCH_MONTH_EN = 'March'
EPOCH_DAY = 12
EPOCH = datetime.datetime(EPOCH_YEAR, EPOCH_MONTH, EPOCH_DAY)

def to_covid(a_datetime):
    """ Convert a datetime object from Gregorian to Covid

        :param a_datetime: datetime.datetime object
        :return: A very stupid string that resembles a date
    """
    ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
    # Terse solution lovingly stolen from SO
    # https://stackoverflow.com/a/20007730
    if a_datetime < EPOCH:
        diff = EPOCH - a_datetime
        diff_days = abs(0 - diff.days + 1)
        sign = '-' if diff_days > 0 else ''
    else:
        diff = a_datetime - EPOCH
        diff_days = EPOCH_DAY + diff.days
        sign = ''
    return (
        f'Gregorian {a_datetime.strftime("%F")} is Covid {EPOCH_MONTH_EN} {sign}{ordinal(diff_days)}, {EPOCH_YEAR}'
    )

DATESTRING = r'''[wW]hat day( of TYOOL 2020)? is (.*)\?'''
COVID_DATE = re.compile(DATESTRING, re.IGNORECASE)
@slackbot.bot.listen_to(COVID_DATE)
def covid_date(message, *groups):
    """ Listen for a question to the bot regarding date transcription from Gregorian to Covid

        :param message: The string message
        :param *groups: Iterable of re.search().groups()
    """
    datestring_maybe = groups[1]
    LOGGER.info('Got a datestring, maybe: "%s"', datestring_maybe)
    try:
        the_date = parser.parse(datestring_maybe)
    except ValueError:
        message.reply(f'"{datestring_maybe}" isn\'t a valid date, ya jerk!')
        return
    message.reply(to_covid(the_date))
