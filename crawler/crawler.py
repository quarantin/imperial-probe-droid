#!/usr/bin/env python3

import sys
import discord
import libswgoh
import traceback

from swgohhelp import SwgohHelpException
from crawlerthread import CrawlerThread

class Crawler(discord.Client):

	async def on_ready(self):

		if not hasattr(self, 'initialized'):
			setattr(self, 'initialized', True)
			print("Starting crawler thread.")
			self.loop.create_task(CrawlerThread().run(self))

		print('Crawler bot ready!')

if __name__ == '__main__':

	import logging
	from config import load_config, setup_logs

	crawler_logger = setup_logs('crawler', 'logs/crawler.log', logging.DEBUG)
	discord_logger = setup_logs('discord', 'logs/crawler-discord.log')

	config = load_config()

	if 'tokens' not in config:
		print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	if 'crawler' not in config['tokens']:
		print('Key "crawler" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	try:
		crawler = Crawler()
		crawler.config = config
		crawler.redis = config.redis
		crawler.logger = crawler_logger
		crawler.run(config['tokens']['crawler'])

	except SwgohHelpException as err:
		print(err)
		print(err.data)

	except:
		print(traceback.format_exc())
