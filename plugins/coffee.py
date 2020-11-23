#!/usr/bin/env python
""" Module for interrupting conversations with coffee messages
"""

import re
import random
import slackbot.bot

COFFEESTRING = r'''(covfefe|coffee|good sludge|fresh pot!)'''
COFFEE = re.compile(COFFEESTRING, re.IGNORECASE)
@slackbot.bot.listen_to(COFFEE)
def coffee(message, *groups):  # pylint: disable=unused-argument
    ''' Just mention coffee or the good sludge or a fresh pot in the bot's presence.
    '''
    strings = [
        'When I am drinking coffee, I always say, "I am going to have another sip of that!" after every sip.',
        '''When I wake up in the morning, the first thing I do is stick my head out my window and yell, "Now '''
        '''it is time for me to drink coffee, the bean-based drink that you can find at the store!"''',
        'I refer to the act of drinking coffee as "getting my sludge on."',
        '''My daughter\'s full legal name is Sludge Junky, The Amazing Coffee-Worshipping Girl, and I require '''
        '''her to speak in the third person.''',
        '''If I go even one hour without getting my sludge on I become belligerent, and I say cruel and '''
        '''unforgivable things such as, "I like it when helpful people get carsick."''',
        '''My body is so amped up on caffeine that doctors have informed me that if my head ever got chopped '''
        '''off by a guillotine, the caffeine in my bloodstream would keep my decapitated body alive long '''
        '''enough for it to pick up my own severed head and punt it over the horizon.''',
        'My favorite thing that I like to do is look at coffee and say, "Now I\'m looking at it."',
        '''Whenever I see a dog on the street, I hold a coffee mug underneath its mouth for a little bit '''
        '''just in case it's the kind of dog that squirts hot jets of coffee out of its mouth.''',
        '''The surgery that doctors must perform to extract a person's entire body from a travel-size French '''
        '''press is named after me.''',
        '''My dream husband is a silent man standing perfectly still in the middle of the woods holding a '''
        '''handful of coffee beans in his clenched fist, and when I kiss him on the cheek, he opens up his '''
        '''hand so that I can look at the beans.''',
        'I once drank so much coffee that a man said to me, "Whoa, buddy, slow down."',
        '''My mother no longer speaks to me because I gave my father's eulogy while wearing a T-shirt that '''
        '''said "I'm Just An Old Curmudgeon Who Loves To Get His Sludge On."''',
        'There is a movie about my life called Often: The Frequency Of Coffee.',
        '''When I see a baby, I will walk right up to that baby and whisper, "Coffee is the sludge I am '''
        '''after" right in that baby's ear.''',
        '''I was once on trial for murder, and 12 different courtroom stenographers got carpal tunnel '''
        '''syndrome from typing the phrase "Your Honor, coffee is the good sludge" so many times.''',
        '''I once wrote a 900-page epic poem called "Sheer Ecstasy" in which I rhymed "French press" with '''
        '''"bench press" over 15,000 times. It was the only rhyme in the poem.''',
        '''The New York Times has already written an article titled "Skeleton Of Nation's Greatest Burden '''
        '''Found Floating In Septic Tank Filled With Coffee," which it will run on the day that I die.'''
    ]
    msg = random.choice(strings)
    if random.randint(0, 100) < 20:
        message.reply(msg)
