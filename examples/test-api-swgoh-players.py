#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import SwgohHelp

async def __main__():
	config = load_config()
	client = SwgohHelp(config)

	ally_codes = [ 349423868 ]
	result = await client.api_swgoh_players({ 'allycodes': ally_codes })
	print(json.dumps(result, indent=4))

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
