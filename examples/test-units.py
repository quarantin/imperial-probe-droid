#!/usr/bin/python3

import json
from config import load_config
from swgohhelp import api_swgoh_units

config = load_config()
ally_codes = [ 349423868 ]
result = api_swgoh_units(config, { 'allycodes': ally_codes})
print(json.dumps(result, indent=4))
