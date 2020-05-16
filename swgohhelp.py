import sys
from datetime import datetime, timedelta

from utils import http_post

DEFAULT_TIMEOUT_SECONDS = 3600

class SwgohHelpException(Exception):
	pass

class SwgohHelp:

	def __init__(self, config, url='https://api.swgoh.help'):
		self.url = url
		self.config = config

	async def get_access_token(self):

		config = self.config

		if 'access_token' in config['swgoh.help']:
			expire = config['swgoh.help']['access_token_expire']
			if expire > datetime.now() + timedelta(seconds=60):
				return config['swgoh.help']['access_token']

		headers = {
			'method': 'post',
			'content-type': 'application/x-www-form-urlencoded',
		}

		data = {
			'username': config['swgoh.help']['username'],
			'password': config['swgoh.help']['password'],
			'grant_type': 'password',
			'client_id': 'abc',
			'client_secret': '123',
		}

		auth_url = '%s/auth/signin' % self.url
		data, error = await http_post(auth_url, headers=headers, data=data)
		if error:
			raise SwgohHelpException('Authentication failed to swgoh.help API: %s' % error)

		if 'access_token' not in data:
			raise SwgohHelpException('Authentication failed: Server returned `%s`' % data)

		config['swgoh.help']['access_token'] = data['access_token']
		config['swgoh.help']['access_token_expire'] = datetime.now() + timedelta(seconds=data['expires_in'])

		if 'debug' in config and config['debug'] is True:
			print('Logged in successfully', file=sys.stderr)

		return config['swgoh.help']['access_token']

	async def get_headers(self):
		access_token = await self.get_access_token()
		return {
			'method': 'post',
			'content-type': 'application/json',
			'authorization': 'Bearer %s' % access_token,
		}

	async def call_api(self, project, url):

		url = self.url + url
		headers = await self.get_headers()

		if 'debug' in self.config and self.config['debug'] is True:
			print("CALL API: %s %s" % (url, project), file=sys.stderr)

		data, error = await http_post(url, headers=headers, json=project)
		if error:
			raise Exception('http_post(%s) failed: %s' % (url, error))

		if 'error' in data:
			error = SwgohHelpException()
			error.title = 'Error from swgoh.help API'
			error.data = data
			raise error

		return data

	async def api_swgoh_players(self, project):

		result = []
		expected_players = len(project['allycodes'])

		new_proj = dict(project)
		new_proj['allycodes'] = list(project['allycodes'])

		while len(result) < expected_players:

			returned = await self.call_api(new_proj, '/swgoh/players')
			for player in returned:
				result.append(player)
				new_proj['allycodes'].remove(player['allyCode'])

		return result

	async def api_swgoh_guilds(self, project):
		return await self.call_api(project, '/swgoh/guilds')

	async def api_swgoh_roster(self, project):
		return await self.call_api(project, '/swgoh/roster')

	async def api_swgoh_units(self, project):
		return await self.call_api(project, '/swgoh/units')

	async def api_swgoh_zetas(self, project):
		return await self.call_api(project, '/swgoh/zetas')

	async def api_swgoh_squads(self, project):
		return await self.call_api(project, '/swgoh/squads')

	async def api_swgoh_events(self, project):
		return await self.call_api(project, '/swgoh/events')

	async def api_swgoh_data(self, project):
		return await self.call_api(project, '/swgoh/data')
