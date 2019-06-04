#!/usr/bin/env python

import asyncio 

from bot import bot
from config import load_config

try:
	config = load_config()

	bot.run(config['token'])

	print('Bot quitting')

except Exception as err:
	print(err)
