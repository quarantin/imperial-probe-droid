#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import *

async def __main__():
	collection = 'unitsList'
	language = 'eng_us'

	config = load_config()

	match = {
		'rarity': 7,
		'obtainable': True,
	}

	test = await api_swgoh_data(config, {
		'collection': collection,
		'language': 'eng_us',
		'match': match,
	})

	print(json.dumps(test, indent=4))

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
