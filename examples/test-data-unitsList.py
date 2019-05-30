#!/usr/bin/python3

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
