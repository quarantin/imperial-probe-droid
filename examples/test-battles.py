#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import call_api

async def __main__():

	config = load_config()

	data = await call_api(config, { 'language': 'eng_us', 'allycodes': [ '349423868' ] }, 'https://api.swgoh.help/swgoh/battles')
	print(json.dumps(data, indent=4))

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
