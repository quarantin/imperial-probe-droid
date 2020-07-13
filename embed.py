import json
import discord

class EmbedManager:

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


	FOOTER = """Please consider signing the petition to have CG unban Ahnaldt101 Kracken account!
https://www.change.org/p/capital-games-capital-games-unban-ahnaldt101-kracken-account"""

	def __init__(self, bot):
		self.bot = bot

	def color(self, name):
		color_code = name in self.COLORS and self.COLORS[name] or self.COLORS['red']
		return discord.Colour(color_code)

	def is_preformated(self, message):
		return message['description'].startswith('```') and message['description'].endswith('```')

	def split_message(self, message, preformated):

		title     = message.pop('title', False)
		author    = message.pop('author', False)
		fields    = message.pop('fields', False)
		thumbnail = message.pop('thumbnail', False)
		timestamp = message.pop('timestamp', False)
		desc      = message.pop('description', False)

		message['title'] = ''
		message['description'] = ''

		count, rest = divmod(len(desc), 2048)
		if count == 0 or rest > 0:
			count += 1

		msgs = [ dict(message) for i in range(0, count) ]

		index = 0
		new_desc = ''
		for line in desc.split('\n'):

			if index >= count:
				break

			if len(new_desc) + len(line) + 1 > 2048 - 6 and preformated is True:
				msgs[index]['description'] = '```%s```' % new_desc
				new_desc = ''
				index += 1

			elif len(new_desc) + len(line) + 1 > 2048:
				msgs[index]['description'] = new_desc
				new_desc = ''
				index += 1

			new_desc += line + '\n'

		else:
			if preformated is True:
				msgs[ len(msgs) - 1 ]['description'] = '```%s```' % new_desc
			else:
				msgs[ len(msgs) - 1 ]['description'] = new_desc

		if title:
			msgs[0]['title'] = title

		if author:
			msgs[0]['author'] = author

		if thumbnail:
			msgs[0]['thumbnail'] = thumbnail

		if fields:

			last_message = msgs[ len(msgs) - 1 ]
			last_message['fields'] = []
			total_length = len(json.dumps(last_message))
			for field in fields:
				field_length = len(json.dumps(field))
				if total_length + field_length < 6000:
					last_message['fields'].append(field)
				else:
					last_message = dict(message)
					last_message['fields'] = [ field ]
					msgs.append(last_message)

				total_length = len(json.dumps(last_message))

		return msgs

	def create(self, msg, timestamp=None, add_sep=False, footer=False):

		from config import load_config
		config = load_config()

		if timestamp is None:
			from utils import local_time
			timestamp = local_time()
			if 'timezone' in config and config['timezone']:
				timestamp = local_time(timezone=config['timezone'])

		if 'color' not in msg:
			msg['color'] = 'blue'

		if 'title' not in msg:
			msg['title'] = ''

		if 'description' not in msg:
			msg['description'] = ''

		preformated = self.is_preformated(msg)

		if 'no-sep' in msg and msg['no-sep'] is True:
			add_sep = False

		if msg['description']:
			sep = add_sep and '\n%s' % config['separator'] or ''
			msg['description'] = '%s%s' % (msg['description'], sep)

		if preformated is True:
			msg['description'] = msg['description'].replace('```', '').replace('`', '')

		embeds = []

		msgs = self.split_message(msg, preformated)

		i = 1
		last_msg = msgs[-1]
		for msg in msgs:

			msg_title = msg['title'] #msg_title = '%s (%d/%d)' % (msg['title'], i, len(msgs))
			#if len(msgs) == 1:
			#	msg_title = msg['title']

			embed = discord.Embed(title=msg_title, colour=self.color(msg['color']), description=msg['description'])

			if 'author' in msg:

				if 'name' not in msg['author']:
					msg['author']['name'] = ''

				if 'icon_url' not in msg['author']:
					msg['author']['icon_url'] = ''

				embed.set_author(name=msg['author']['name'], icon_url=msg['author']['icon_url'])

			if 'thumbnail' in msg and 'url' in msg['thumbnail']:
				embed.set_thumbnail(url=msg['thumbnail']['url'])

			if 'fields' in msg:
				for field in msg['fields']:

					if 'name' not in field:
						field['name'] = ''

					if 'value' not in field:
						field['value'] = ''

					if 'inline' not in field:
						field['inline'] = False

					embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

			if msg == last_msg:
				#embed.set_footer(text=self.FOOTER)
				if footer:
					embed.timestamp = timestamp
				if 'image' in msg and 'url' in msg['image']:
					embed.set_image(url=msg['image']['url'])
			else:
				embed.set_footer(text='')

			#if not footer:
			#	embed.set_footer(text='')

			embeds.append(embed)

			i += 1

		return embeds

	async def send(self, channel, message):

		embeds = self.create(message)
		for embed in embeds:
			status, error = await self.bot.sendmsg(channel, message='', embed=embed)
			if not status:
				self.bot.logger.error('Could not send to channel %s: %s' % (channel, error))
