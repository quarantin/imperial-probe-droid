#!/usr/bin/python3

import json
from config import load_config
from swgohhelp import api_swgoh_players, api_crinolo, fetch_crinolo_stats

config = load_config()
ally_codes = [ 349423868, 913624995 ]
stats, players = fetch_crinolo_stats(config, ally_codes)
print(json.dumps(stats, indent=4))
