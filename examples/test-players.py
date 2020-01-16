#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from config import load_config
from swgohhelp import fetch_players

config = load_config()
ally_codes = [ 349423868 ]
result = fetch_players(config, ally_codes)
print(json.dumps(result, indent=4))
