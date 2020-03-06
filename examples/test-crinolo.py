#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import api_swgoh_players, api_crinolo, fetch_crinolo_stats

async def __main__():
	config = load_config()
	ally_codes = [ 349423868, 913624995 ]
	stats, players = await fetch_crinolo_stats(config, ally_codes)
	print(json.dumps(stats, indent=4))

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
