#!/usr/bin/python3

import json
from config import load_config
from swgohhelp import fetch_guilds

config = load_config()
ally_codes = [ '349423868' ]
result = fetch_guilds(config, ally_codes)
print(json.dumps(result, indent=4))
