#!/usr/bin/python3

import asyncio 

from bot import bot
from config import config, load_config

try:
	load_config()

	bot.loop.run_until_complete(bot.start(config['token']))

except Exception as err:
	print(err)
