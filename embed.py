#!/usr/bin/python3

import discord
from utils import now

COLORS = {
	'blue':       0x268bd2,
	'cyan':       0x2aa198,
	'dark-gray':  0x586e75,
	'green':      0x859900,
	'light-gray': 0x839496,
	'orange':     0xcb4b16,
	'red':        0xdc322f,
	'yellow':     0xb58900,
}

def color(name):
	color_code = name in COLORS and COLORS[name] or COLORS['red']
	return discord.Colour(color_code)

def new_embed(config, msg, timestamp=None):

	if timestamp is None:
		timestamp = now(config['timezone'])

	if 'color' not in msg:
		msg['color'] = 'blue'

	if 'title' not in msg:
		msg['title'] = ''

	if 'description' not in msg:
		msg['description'] = ''
	
	if msg['description']:
		msg['description'] = '%s\n%s' % (msg['description'], config['separator'])

	embed = discord.Embed(title=msg['title'], colour=color(msg['color']), description=msg['description'], timestamp=timestamp)

	if 'author' in msg:

		if 'name' not in msg['author']:
			msg['author']['name'] = ''

		if 'icon_url' not in msg['author']:
			msg['author']['icon_url'] = ''

		embed.set_author(name=msg['author']['name'], icon_url=msg['author']['icon_url'])

	if 'image' in msg:
		embed.set_image(url=msg['image'])

	if 'thumbnail' in msg:
		embed.set_thumbnail(url=msg['thumbnail'])

	if 'fields' in msg:
		for field in msg['fields']:

			if 'name' not in field:
				field['name'] = ''

			if 'value' not in field:
				field['value'] = ''

			if 'inline' not in field:
				field['inline'] = False

			embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

	print(msg)
	return embed
