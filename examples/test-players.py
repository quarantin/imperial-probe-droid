#!/usr/bin/python3

import json
from config import load_config
from swgohhelp import fetch_players

config = load_config()
ally_codes = [ 349423868 ]
result = fetch_players(config, ally_codes)
print(json.dumps(result, indent=4))
