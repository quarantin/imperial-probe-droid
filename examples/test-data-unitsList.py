#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import *

collection = 'unitsList'
language = 'eng_us'

config = load_config()

match = {
	'rarity': 7,
	'obtainable': True,
}

test = api_swgoh_data(config, {
	'collection': collection,
	'language': 'eng_us',
	'match': match,
})

print(json.dumps(test, indent=4))
