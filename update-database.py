#!/usr/bin/env python

import os
import sys
import json
import traceback
from recos import fetch_all_recos
from utils import http_get, load_json, dump_json, fix_swgohgg_url
from bs4 import BeautifulSoup

import DJANGO
from django.db import transaction
from swgoh.models import *

class CacheUpdater:

	urls = {
		'cache/characters.json': 'https://swgoh.gg/api/characters/',
		'cache/ships.json':      'https://swgoh.gg/api/ships/',
		'cache/gear.json':       'https://swgoh.gg/api/gear/'
	}

	base_projects = [

		{
			'collection': 'skillList',
			'project': {
				'id': 1,
				'abilitiyReference': 1,
				'isZeta': 1,
			},
		},
		{
			'collection': 'unitsList',
			'match': {
				'rarity': 7,
				'obtainable': True,
			},
		},
	]

	lang_projects = [

		{
			'collection': 'abilityList',
			'project': {
				'id': 1,
				'nameKey': 1,
				'descKey': 1,
				'tierList': {
					'descKey': 1,
				},
			},
		},
		{
			'collection': 'equipmentList',
			'project': {
				'id': 1,
				'nameKey': 1,
			},
		},
		{
			'collection': 'unitsList',
			'project': {
				'baseId': 1,
				'nameKey': 1,
			},
			'match': {
				'rarity': 7,
				'obtainable': True,
			},
		},
	]

	def __init__(self, config):
		from swgohhelp import SwgohHelp
		self.client = SwgohHelp(config)
		self.version_url = 'https://api.swgoh.help/version'
		self.version_filename = 'cache/version.json'

	def get_version(self):

		try:
			return load_json(self.version_filename)

		except:
			return None

	async def get_remote_version(self):

		try:
			response, error = await http_get(self.version_url)
			if error is False:
				return response.json()
		except:
			print(traceback.format_exc())

		return None

	def update_version(self, version):
		dump_json(self.version_filename, version)

	async def update(self, version):

		for filename, url in self.urls.items():
			response, error = await http_get(url)
			if not response:
				raise Exception('http_get failed!')

			fin = open(filename, 'w')
			fin.write(response.text)
			fin.close()

		# First download all base files
		for base_project in self.base_projects:

			project = dict(base_project)
			if 'project' in project:
				project.pop('project')

			print('Downloading base collection `%s`...' % project['collection'])
			data = await self.client.api_swgoh_data(project)

			filename = 'cache/%s.json' % project['collection']
			with open(filename, 'w') as fout:
				fout.write(json.dumps(data))

		# Then download language specific information
		for language, lang_code, lang_flag, lang_name in Player.LANGS:
			for lang_project in self.lang_projects:

				project = dict(lang_project)
				project['language'] = language

				print('Downloading %s collection `%s`...' % (language, project['collection']))
				data = await self.client.api_swgoh_data(project)

				filename = 'cache/%s_%s.json' % (project['collection'], language)
				with open(filename, 'w') as fout:
					fout.write(json.dumps(data))

		self.update_version(version)

class DatabaseUpdater:

	UNITS_TO_IGNORE = [
		'AMILYNHOLDO_RADDUS',
		'AWAKENEDREY',
		'CAPITALFINALIZER_EVENT',
		'CAPITALRADDUS_EVENT',
		'FOTF_DEVASTATOR',
		'FOTF_VADER',
		'GENERALHUX_EVENT',
		'GRIEVOUS_MARQUEE',
		'KYLOREN_DUEL',
		'KYLORENUNMASKED_GLEVENT',
		'REY_DUEL',
		'REYJEDITRAINING_GLEVENT',
		'VULTUREDROID_tb',
	]

	WANTED_KEYS = {
		'UnitStat_Accuracy':                    'Potency',
		'UnitStat_Armor':                       'Armor',
		'UnitStat_CriticalDamage':              'Critical Damage',
		'UnitStat_Defense':                     'Defense',
		'UnitStat_DefensePenetration':          'Defense Penetration',
		'UnitStat_Health':                      'Health',
		'UnitStat_HealthSteal':                 'Health Steal',
		'UnitStat_MaxShield':                   'Protection',
		'UnitStat_Offense':                     'Offense',
		'UnitStat_DodgeNegateRating':           'Physical Accuracy',
		'UnitStat_AttackCriticalNegateRating':  'Physical Critical Avoidance',
		'UnitStat_AttackCriticalRating_TU5V':   'Physical Critical Chance',
		'UnitStat_DeflectionNegateRating':      'Special Accuracy',
		'UnitStat_AbilityCriticalNegateRating': 'Special Critical Avoidance',
		'UnitStat_Resistance':                  'Tenacity',
		'UnitStat_Speed':                       'Speed',
		'UnitStat_Suppression':                 'Resistance',
		'UnitStat_SuppressionPenetration':      'Resistance Penetration',
	}

	def __init__(self, config):
		self.config = config
		for i in range(1, 13):
			key = 'Unit_Tier%02d' % i
			self.WANTED_KEYS[key] = False

	def parse_translations_name(self, collection, key, context, language):

		print('Parsing names translations (%s)...' % language)

		filename = 'cache/%s_%s.json' % (collection, language)
		with open(filename, 'r') as fin:
			jsondata = json.loads(fin.read())
			with transaction.atomic():
				for entry in jsondata:

					obj, created = Translation.objects.update_or_create(string_id=entry[key], context=context, language=language)
					if obj.translation != entry['nameKey']:
						obj.translation = entry['nameKey']
						obj.save()

	def parse_translations_desc(self, collection, key, context, language):

		print('Parsing descriptions translations (%s)...' % language)

		filename = 'cache/%s_%s.json' % (collection, language)
		with open(filename, 'r') as fin:
			jsondata = json.loads(fin.read())
			with transaction.atomic():
				for entry in jsondata:

					tier_index = 1
					string_id = '%s_tier%02d' % (entry[key], tier_index)
					obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language)
					if obj.translation != entry['descKey']:
						obj.translation = entry['descKey']
						obj.save()

					tier_index = 2
					for tier in entry['tierList']:

						string_id = '%s_tier%02d' % (entry[key], tier_index)
						obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language)
						if obj.translation != tier['descKey']:
							obj.translation = tier['descKey']
							obj.save()

						tier_index += 1

	def parse_localization_files(self):

		context = 'localization'
		for language, lang_code, lang_flag, lang_name in Player.LANGS:

			filename = 'cache/Loc_%s.txt' % language.upper()
			if not os.path.exists(filename):
				print('Skipping missing translation file: %s' % filename)
				continue

			with open(filename, 'r') as fin:
				for line in fin:
					line = line.strip()
					if line.startswith('#'):
						continue

					string_id, translation = line.split('|')
					if string_id in self.WANTED_KEYS:
						if self.WANTED_KEYS[string_id] is not False:
							string_id = self.WANTED_KEYS[string_id]

						obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language, )
						if obj.translation != translation:
							obj.translation = translation
							obj.save()
							print('Updated %s translation for %s' % (lang_name, string_id))

	def parse_units(self):

		print('Parsing units...')

		names = load_json('cache/unitsList_eng_us.json')
		unit_names = { x['baseId']: x['nameKey'] for x in names }

		ship_crews = BaseUnit.get_ship_crews()

		self.units = {}
		with transaction.atomic():

			for filename in [ 'unitsList.json' ]:
				units = load_json('cache/%s' % filename)
				for unit in units:

					base_id = unit['baseId']

					if base_id in self.UNITS_TO_IGNORE:
						continue

					if base_id in self.units:
						raise Exception('Duplicate base ID for character: %s' % base_id)

					char = {}

					char['base_id'] = base_id
					char['name'] = base_id in unit_names and unit_names[base_id] or base_id
					char['alignment'] = unit['forceAlignment']
					char['is_ship'] = (unit['combatType'] == BaseUnit.COMBAT_TYPES[1][0])

					try:
						base_unit = BaseUnit.objects.get(base_id=base_id)
						BaseUnit.objects.filter(pk=base_unit.pk).update(**char)

					except BaseUnit.DoesNotExist:
						base_unit = BaseUnit(**char)
						base_unit.save()

					self.units[base_unit.base_id] = base_unit

					categories = unit.pop('categoryIdList')
					for category in categories:
						faction = BaseUnitFaction.is_supported_faction(category)
						if faction:
							obj, created = BaseUnitFaction.objects.update_or_create(unit=base_unit, faction=faction)

	def parse_gear(self):

		print('Parsing gears...')

		with transaction.atomic():
			gears = load_json('cache/gear.json')
			for gear in gears:

				stats       = gear.pop('stats')
				recipes     = gear.pop('recipes')
				ingredients = gear.pop('ingredients')

				gear['url']   = fix_swgohgg_url(gear['url'])
				gear['image'] = fix_swgohgg_url(gear['image'])

				try:
					equip = Gear.objects.get(base_id=gear['base_id'])

				except Gear.DoesNotExist:
					equip = Gear(base_id=gear['base_id'])

				for key, val in gear.items():
					if hasattr(equip, key):
						setattr(equip, key, val)

				equip.save()

	def parse_gear_levels(self):

		print('Parsing gear levels...')

		with transaction.atomic():

			filename = 'cache/characters.json'
			characters = load_json(filename)
			for character in characters:

				base_id = character['base_id']
				base_unit = self.units[base_id]

				if base_id in self.UNITS_TO_IGNORE:
					continue

				if 'gear_levels' not in character:
					raise Exception('Missing gear level for character %s' % character['name'])

				gear_levels = character['gear_levels']
				for gear_level in gear_levels:

					slot = 1
					tier = gear_level['tier']

					for gear_id in gear_level['gear']:

						gear = Gear.objects.get(base_id=gear_id)

						try:
							created = False
							obj = BaseUnitGear.objects.get(unit=base_unit, tier=tier, slot=slot)

						except BaseUnitGear.DoesNotExist:
							created = True
							obj = BaseUnitGear(unit=base_unit, tier=tier, slot=slot)

						if created or obj.gear != gear:
							obj.gear = gear
							obj.save()

						slot += 1

	def parse_skills(self):

		print('Parsing skills...')

		filename = 'cache/skillList.json'
		skill_list = load_json(filename)
		skills = {}
		for skill in skill_list:
			skill_id = skill['id']
			skills[skill_id] = skill

		filename = 'cache/abilityList_eng_us.json'
		ability_list = load_json(filename)
		max_tiers = {}
		for ability in ability_list:
			ability_ref = ability['id']
			max_tiers[ability_ref] = len(ability['tierList']) + 1

		filename = 'cache/unitsList.json'
		units = load_json(filename)
		with transaction.atomic():
			for unit in units:
				base_id = unit['baseId']

				if base_id.startswith('PVE_') or base_id in self.UNITS_TO_IGNORE:
					continue

				try:
					real_unit = BaseUnit.objects.get(base_id=base_id)
					unit_skills = unit['skillReferenceList']

					if 'crewList' in unit:
						for crew_member in unit['crewList']:
							unit_skills.extend(crew_member['skillReferenceList'])

					for skill in unit_skills:

						skill_id = skill['skillId']
						ability = skills[skill_id]
						ability_ref = ability['abilityReference']

						try:
							obj = BaseUnitSkill.objects.get(skill_id=skill_id)

						except BaseUnitSkill.DoesNotExist:
							obj = BaseUnitSkill(skill_id=skill_id)


						obj.ability_ref = ability_ref
						obj.max_tier = max_tiers[ability_ref]
						obj.is_zeta = ability['isZeta']
						obj.unit = real_unit

						obj.save()

				except BaseUnit.DoesNotExist:
					print("WARN: Missing unit from DB: %s" % base_id)
					continue

	async def parse_zeta_report(self):

		print('Parsing zeta report')

		url = 'https://swgoh.gg/stats/ability-report/?page=%d'
		try:
			response, error = await http_get(url % 1)
			soup = BeautifulSoup(response.content, 'html.parser')
			pagination_ul = soup.find('ul', { 'class': [ 'pagination', 'm-t-0' ] })
			pages = int(pagination_ul.find('a').text.replace('Page 1 of ', ''))

			page = 1
			while page < pages + 1:

				lis = soup.find_all('li', { 'class': 'character' })
				for li in lis:
					imgs = li.find_all('img')

					base_id = os.path.basename(os.path.dirname(imgs[0]['src']))
					skill_id = os.path.basename(os.path.dirname(imgs[1]['src']))

					div = li.find('div', { 'class': 'zeta-row' })
					zr = div.find_all('div')

					total_zetas      = int(zr[0].find('h3').text.replace(',', ''))
					of_all_zetas     = float(zr[1].find('h3').text.replace('%', ''))
					of_all_this_unit = float(zr[2].find('h3').text.replace('%', ''))
					of_g11_this_unit = float(zr[3].find('h3').text.replace('%', ''))

					try:
						unit = BaseUnit.objects.get(base_id=base_id)
					except BaseUnit.DoesNotExist:
						print('Could not find unit with base ID: %s' % base_id)
						continue

					try:
						zeta = ZetaStat.objects.get(unit=unit, skill_id=skill_id)
						zeta.total_zetas = total_zetas
						zeta.of_all_zetas = of_all_zetas
						zeta.of_all_this_unit = of_all_this_unit
						zeta.of_g11_this_unit = of_g11_this_unit

					except ZetaStat.DoesNotExist:
						zeta = ZetaStat(unit=unit, skill_id=skill_id, total_zetas=total_zetas, of_all_zetas=of_all_zetas, of_all_this_unit=of_all_this_unit, of_g11_this_unit=of_g11_this_unit)

					zeta.save()

				if page == pages:
					break

				page += 1
				response, error = await http_get(url % page)
				if not response or error:
					print('ERROR: %s' % error)
					return

				soup = BeautifulSoup(response.content, 'html.parser')

		except:
			print(traceback.format_exc())

	async def parse_gear13_report(self):

		print('Parsing gear level 13 report...')

		url = 'https://swgoh.gg/characters/data/g13/'
		try:
			response, error = await http_get(url)
			soup = BeautifulSoup(response.content, 'html.parser')
			rows = soup.find(id='characters').find('tbody').find_all('tr')
			for row in rows:

				cols = row.find_all('td')

				unit_name   = cols[0].text.strip()
				g13_count   = int(cols[1].text)
				total_count = int(cols[2].text)
				percentage  = float(cols[3].text.replace('%', ''))

				try:
					unit = BaseUnit.objects.get(name=unit_name)

				except BaseUnit.DoesNotExist:
					print("Could not find unit with name '%s'. Skipping." % unit_name)
					continue

				try:
					g13_stat = Gear13Stat.objects.get(unit=unit)
					g13_stat.g13_count = g13_count
					g13_stat.total_count = total_count
					g13_stat.percentage = percentage

				except Gear13Stat.DoesNotExist:
					g13_stat = Gear13Stat(unit=unit, g13_count=g13_count, total_count=total_count, percentage=percentage)

				g13_stat.save()

		except:
			print(traceback.format_exc())

	async def parse_relic_report(self):

		print('Parsing relic report...')

		url = 'https://swgoh.gg/characters/data/relics/'
		try:
			response, error = await http_get(url)
			soup = BeautifulSoup(response.content, 'html.parser')
			rows = soup.find(id='characters').find('tbody').find_all('tr')
			for row in rows:

				cols = row.find_all('td')

				unit_name = cols[0].text.strip()
				unit = BaseUnit.objects.get(name=unit_name)
				try:
					s = RelicStat.objects.get(unit=unit)

				except RelicStat.DoesNotExist:
					s = RelicStat(unit=unit)

				s.relic1 = int(cols[1].text)
				s.relic2 = int(cols[2].text)
				s.relic3 = int(cols[3].text)
				s.relic4 = int(cols[4].text)
				s.relic5 = int(cols[5].text)
				s.relic6 = int(cols[6].text)
				s.relic7 = int(cols[7].text)
				s.g13_units = int(cols[22].text) or 1

				s.relic7_percentage = 100 * ((s.relic7) / s.g13_units)
				s.relic6_percentage = 100 * ((s.relic7 + s.relic6) / s.g13_units)
				s.relic5_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5) / s.g13_units)
				s.relic4_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4) / s.g13_units)
				s.relic3_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3) / s.g13_units)
				s.relic2_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3 + s.relic2) / s.g13_units)
				s.relic1_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3 + s.relic2 + s.relic1) / s.g13_units)

				s.save()

		except:
			print(traceback.format_exc())

	def parse_rss_feeds(self):

		print('Parsing RSS feeds...')

		if 'feeds' not in self.config:
			print('No RSS feed defined in config.json')
			return

		for feed_name, feed_url in self.config['feeds'].items():

			try:
				feed = NewsFeed.objects.get(name=feed_name, url=feed_url)

			except NewsFeed.DoesNotExist:
				print("Saving RSS feed %s (%s)" % (feed_name, feed_url))
				feed = NewsFeed(name=feed_name, url=feed_url)
				feed.save()

	async def save_all_recos(self):

		print('Parsing mod recommendations...')

		with transaction.atomic():
			recos = await fetch_all_recos()
			ModRecommendation.objects.all().delete()
			for reco in recos:

				base_id = reco.pop('base_id')
				reco['character'] = BaseUnit.objects.get(base_id=base_id)
				obj, created = ModRecommendation.objects.get_or_create(**reco)
				# TODO Why are mod recommendations created every time, but the total count does not increase?
				#print(reco)
				#if created is True:
				#	print('Added new mod recommendation for %s' % base_id)

	def get_version(self):

		try:
			o = Translation.objects.get(string_id='version')
			return {
				'game': o.context,
				'language': o.translation,
			}

		except Translation.DoesNotExist:
			return None

	def update_version(self, version):

		try:
			o = Translation.objects.get(string_id='version')

		except Translation.DoesNotExist:
			o = Translation(string_id='version')

		o.language = 'eng_us'
		o.context = version['game']
		o.translation = version['language']

		o.save()

	async def update(self, version):

		self.parse_rss_feeds()
		self.parse_units()
		self.parse_gear()
		self.parse_gear_levels()
		self.parse_skills()
		await self.parse_zeta_report()
		await self.parse_gear13_report()
		await self.parse_relic_report()
		self.parse_localization_files()

		await self.save_all_recos()

		for language, lang_code, lang_flag, lang_name in Player.LANGS:

			print('Parsing %s translations...' % language.lower())

			self.parse_translations_name('abilityList',   'id',     'abilities',  language)
			self.parse_translations_name('equipmentList', 'id',     'gear-names', language)
			self.parse_translations_name('unitsList',     'baseId', 'unit-names', language)
			self.parse_translations_desc('abilityList',   'id',     'skill-desc', language)

		self.update_version(version)

class Updater:

	def __init__(self, config):
		self.cache = CacheUpdater(config)
		self.database = DatabaseUpdater(config)

	async def update(self, forced=False):

		remote_version = await self.cache.get_remote_version()
		if not remote_version:
			msg = 'FATAL: Failed to retrieve remote version!'
			print(msg)
			print(traceback.format_exc())
			raise Exception(msg)

		local_version = self.cache.get_version()
		database_version = self.database.get_version()

		up_to_date = False
		if remote_version == database_version and local_version and not forced:
			print('Nothing to update!\n')
			up_to_date = True

		elif forced:
			print('Forced update!\n')

		else:
			print('New version found, updating!\n')

		print('Remote cache version: %s' % remote_version)
		print('Local cache version:  %s' % local_version)
		print('Database version:     %s' % database_version)

		if up_to_date:
			sys.exit(1)

		if remote_version != local_version:
			print('Updating cache with new game assets...')
			await self.cache.update(remote_version)
			print('OK')
		else:
			print('Not updating cache (up-to-date)')

		if remote_version != database_version or forced:
			print('Updating database with new game assets...')
			await self.database.update(remote_version)
			print('OK')
		else:
			print('Not updating database (up-to-date)')

async def __main__():

	forced = '-f' in sys.argv or '--force' in sys.argv

	from config import load_config
	config = load_config()

	updater = Updater(config)
	await updater.update(forced=forced)

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
