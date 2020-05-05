#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import api_swgoh_data

async def __main__():

	config = load_config()

	test = await api_swgoh_data(config, {
		'collection': 'abilityList',
		'language': 'eng_us',
		#'project': {'id': 1, 'nameKey': 1, 'descKey': 1, 'tierList': {'descKey': 1}},
		#'match': { 'rarity': 7, 'obtainable': True },
	})
	print(json.dumps(test, indent=4))
	#for data in test:
	#	print(data)

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
