""""
   MTTOD: utils/clean_dataset.py

   implements dataset cleaning preprocess

   This code is referenced from thu-spmi's damd-multiwoz repository:
   (https://github.com/thu-spmi/damd-multiwoz/blob/master/clean_dataset.py)

   Copyright 2021 ETRI LIRS, Yohan Lee
   Copyright 2019 Yichi Zhang

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import os
import re
import json
import random
import logging
from tqdm import tqdm

from utils import definitions

logger = logging.getLogger(__name__)


def clean_text(text, mapping_pair=None, domain=None):
    text = text.strip()
    text = text.lower()

    ##### my code
    text = text.replace("`", "")
    ##### my code (end)

    text = text.replace(u"’", "'")
    text = text.replace(u"‘", "'")
    text = text.replace(';', ',')
    text = text.replace('"', ' ')
    text = text.replace('/', ' and ')
    text = text.replace("don't", "do n't")
    text = clean_time(text)
    baddata = {r'c\.b (\d), (\d) ([a-z])\.([a-z])': r'cb\1\2\3\4',
               'c.b. 1 7 d.y': 'cb17dy',
               'c.b.1 7 d.y': 'cb17dy',
               'c.b 25, 9 a.q': 'cb259aq',
               'isc.b 25, 9 a.q': 'is cb259aq',
               'c.b2, 1 u.f': 'cb21uf',
               'c.b 1,2 q.a': 'cb12qa',
               '0-122-336-5664': '01223365664',
               'postcodecb21rs': 'postcode cb21rs',
               r'i\.d': 'id',
                        ' i d ': 'id',
                        'Telephone:01223358966': 'Telephone: 01223358966',
                        'depature': 'departure',
                        'depearting': 'departing',
                        '-type': ' type',
                        r"b[\s]?&[\s]?b": "bed and breakfast",
                        "b and b": "bed and breakfast",
                        r"guesthouse[s]?": "guest house",
                        r"swimmingpool[s]?": "swimming pool",
                        "wo n\'t": "will not",
                        " \'d ": " would ",
                        " \'m ": " am ",
                        " \'re' ": " are ",
                        " \'ll' ": " will ",
                        " \'ve ": " have ",
                        r'^\'': '',
                        r'\'$': '',
               }
    for tmpl, good in baddata.items():
        text = re.sub(tmpl, good, text)

    if domain is None or domain != "people":
        text = re.sub(r'([a-zT]+)\.([a-z])', r'\1 . \2',
                      text)   # 'abc.xyz' -> 'abc . xyz'
        text = re.sub(r'(\w+)\.\.? ', r'\1 . ', text)   # if 'abc. ' -> 'abc . '

    if mapping_pair is not None:
        for (fromx, tox) in mapping_pair:
            text = ' ' + text + ' '
            text = text.replace(' ' + fromx + ' ', ' ' + tox + ' ')[1:-1]

    return text


def clean_time(utter):
    # 9 am -> 9am
    utter = re.sub(r'(\d+) ([ap]\.?m)',
                   lambda x: x.group(1) + x.group(2), utter)
    utter = re.sub(r'((?<!\d)\d:\d+)(am)?', r'0\1', utter)
    utter = re.sub(r'((?<!\d)\d)am', r'0\1:00', utter)
    utter = re.sub(r'((?<!\d)\d)pm', lambda x: str(
        int(x.group(1))+12)+':00', utter)
    utter = re.sub(r'(\d+)(:\d+)pm',
                   lambda x: str(int(x.group(1))+12)+x.group(2), utter)
    utter = re.sub(r'(\d+)a\.?m', r'\1', utter)
    return utter


def clean_slot_values(domain, slot, value, mapping_pair=None):
    value = clean_text(value, mapping_pair, domain)
    if not value:
        value = ''
    elif value == 'not mentioned':
        value = ''
        # value = 'not mentioned' # if in DST setting
    elif domain == 'attraction':
        if slot == 'name':
            if value == 't':
                value = ''
            if value == 'trinity':
                value = 'trinity college'
        elif slot == 'area':
            if value in ['town centre', 'cent', 'center', 'ce']:
                value = 'centre'
            elif value in ['ely', 'in town', 'museum', 'norwich', 'same area as hotel']:
                value = ""
            elif value in ['we']:
                value = "west"
        elif slot == 'type':
            if value in ['m', 'mus', 'musuem']:
                value = 'museum'
            elif value in ['art', 'architectural']:
                value = "architecture"
            elif value in ['churches']:
                value = "church"
            elif value in ['coll']:
                value = "college"
            elif value in ['concert', 'concerthall']:
                value = 'concert hall'
            elif value in ['night club']:
                value = 'nightclub'
            elif value in ['mutiple sports', 'mutliple sports', 'sports', 'galleria']:
                value = 'multiple sports'
            elif value in ['ol', 'science', 'gastropub', 'la raza']:
                value = ''
            elif value in ['swimmingpool', 'pool']:
                value = 'swimming pool'
            elif value in ['fun']:
                value = 'entertainment'

    elif domain == 'hotel':
        if slot == 'area':
            if value in ['cen', 'centre of town', 'near city center', 'center']:
                value = 'centre'
            elif value in ['east area', 'east side']:
                value = 'east'
            elif value in ['in the north', 'north part of town']:
                value = 'north'
            elif value in ['we']:
                value = "west"
        elif slot == "day":
            if value == "monda":
                value = "monday"
            elif value == "t":
                value = "tuesday"
        elif slot == 'name':
            if value == 'uni':
                value = 'university arms hotel'
            elif value == 'university arms':
                value = 'university arms hotel'
            elif value == 'acron':
                value = 'acorn guest house'
            elif value == 'ashley':
                value = 'ashley hotel'
            elif value == 'arbury lodge guesthouse':
                value = 'arbury lodge guest house'
            elif value == 'la':
                value = 'la margherit'
            elif value == 'no':
                value = ''
        elif slot == 'internet':
            if value == 'does not':
                value = 'no'
            elif value in ['y', 'free', 'free internet']:
                value = 'yes'
            elif value in ['4']:
                value = ''
        elif slot == 'parking':
            if value == 'n':
                value = 'no'
            elif value in ['free parking']:
                value = 'yes'
            elif value in ['y']:
                value = 'yes'
        elif slot in ['pricerange', 'price range']:
            slot = 'pricerange'
            if value == 'moderately':
                value = 'moderate'
            elif value in ['any']:
                value = "do n't care"
            elif value in ['any']:
                value = "do n't care"
            elif value in ['inexpensive']:
                value = "cheap"
            elif value in ['2', '4']:
                value = ''
        elif slot == 'stars':
            if value == 'two':
                value = '2'
            elif value == 'three':
                value = '3'
            elif value in ['4-star', '4 stars', '4 star', 'four star', 'four stars']:
                value = '4'
        elif slot == 'type':
            if value == '0 star rarting':
                value = ''
            elif value == 'guesthouse':
                value = 'guest house'
            elif value not in ['hotel', 'guest house', "do n't care"]:
                value = ''
    elif domain == 'restaurant':
        if slot == "area":
            if value in ["center", 'scentre', "center of town", "city center",
                         "cb30aq", "town center", 'centre of cambridge', 'city centre']:
                value = "centre"
            elif value == "west part of town":
                value = "west"
            elif value == "n":
                value = "north"
            elif value in ['the south']:
                value = 'south'
            elif value not in ['centre', 'south', "do n't care", 'west', 'east', 'north']:
                value = ''
        elif slot == "day":
            if value == "monda":
                value = "monday"
            elif value == "t":
                value = "tuesday"
        elif slot in ['pricerange', 'price range']:
            slot = 'pricerange'
            if value in ['moderately', 'mode', 'mo']:
                value = 'moderate'
            elif value in ['not']:
                value = ''
            elif value in ['inexpensive', 'ch']:
                value = "cheap"
        elif slot == "food":
            if value == "barbecue":
                value = "barbeque"
        elif slot == "pricerange":
            if value == "moderately":
                value = "moderate"
        elif slot == "time":
            if value == "9:00":
                value = "09:00"
            elif value == "9:45":
                value = "09:45"
            elif value == "1330":
                value = "13:30"
            elif value == "1430":
                value = "14:30"
            elif value == "9:15":
                value = "09:15"
            elif value == "9:30":
                value = "09:30"
            elif value == "1830":
                value = "18:30"
            elif value == "9":
                value = "09:00"
            elif value == "2:00":
                value = "14:00"
            elif value == "1:00":
                value = "13:00"
            elif value == "3:00":
                value = "15:00"
    elif domain == 'taxi':
        if slot in ['arriveBy', 'arrive by']:
            slot = 'arriveby'
            if value == '1530':
                value = '15:30'
            elif value == '15 minutes':
                value = ''
        elif slot in ['leaveAt', 'leave at']:
            slot = 'leaveat'
            if value == '1:00':
                value = '01:00'
            elif value == '21:4':
                value = '21:04'
            elif value == '4:15':
                value = '04:15'
            elif value == '5:45':
                value = '05:45'
            elif value == '0700':
                value = '07:00'
            elif value == '4:45':
                value = '04:45'
            elif value == '8:30':
                value = '08:30'
            elif value == '9:30':
                value = '09:30'
            value = value.replace(".", ":")

    elif domain == 'train':
        if slot in ['arriveBy', 'arrive by']:
            slot = 'arriveby'
            if value == '1':
                value = '01:00'
            elif value in ['does not care', 'doesnt care', "doesn't care"]:
                value = "do n't care"
            elif value == '8:30':
                value = '08:30'
            elif value == 'not 15:45':
                value = ''
            value = value.replace(".", ":")
        elif slot == 'day':
            if value == 'doesnt care' or value == "doesn't care":
                value = "do n't care"
        elif slot in ['leaveAt', 'leave at']:
            slot = 'leaveat'
            if value == '2:30':
                value = '02:30'
            elif value == '7:54':
                value = '07:54'
            elif value == 'after 5:45 pm':
                value = '17:45'
            elif value in ['early evening', 'friday', 'sunday', 'tuesday', 'afternoon']:
                value = ''
            elif value == '12':
                value = '12:00'
            elif value == '1030':
                value = '10:30'
            elif value == '1700':
                value = '17:00'
            elif value in ['does not care', 'doesnt care', 'do nt care', "doesn't care"]:
                value = "do n't care"

            value = value.replace(".", ":")
    if value in ['dont care', "don't care", "do nt care", "doesn't care"]:
        value = "do n't care"
    if definitions.NORMALIZE_SLOT_NAMES.get(slot):
        slot = definitions.NORMALIZE_SLOT_NAMES[slot]
    return slot, value


if __name__ == "__main__":
    text = "The train id is TR0192  and the cost is 17.60".lower()

    print(clean_text(text))
