#!/usr/bin/python3

import json
from config import load_config
from swgohhelp import api_swgoh_data

config = load_config()

test = api_swgoh_data(config, {
	'collection': 'equipmentList',
	#'language': 'eng_us',
	'language': 'fre_fr',
})
print(json.dumps(test, indent=4))
#for data in test:
#	print(data)
