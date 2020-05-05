#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import api_crinolo

async def __main__():

	if len(sys.argv) < 2:
		print('Usage: %s <json>' % sys.argv[0])
		sys.exit(-1)

	config = load_config()

	#ally_codes = [ 349423868, 913624995 ]

	fin = open(sys.argv[1], 'r')
	players = json.loads(fin.read())
	fin.close()

	stats = await api_crinolo(config, players)
	print(json.dumps(stats, indent=4))

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
