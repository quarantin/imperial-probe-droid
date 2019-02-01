#!/usr/bin/python3

import os
import sys
import pytz
import subprocess
from datetime import datetime

PERCENT_STATS = [
	'%armor',
	'%critical-damage',
	'%physical-critical-chance',
	'%potency',
	'%resistance',
	'%special-critical-chance',
	'%tenacity',
]

FORMAT_LUT = {
	'%gear':  'gear_level',
	'%id':    'base_id',
	'%level': 'level',
	'%name':  'name',
	'%power': 'power',
	'%stars': 'rarity',
}

STATS_LUT = {
    '%health':                      '1',
    '%strength':                    '2',
    '%agility':                     '3',
    '%tactics':                     '4',
    '%speed':                       '5',
    '%physical-damage':             '6',
    '%special-damage':              '7',
    '%armor':                       '8',
    '%resistance':                  '9',
    '%armor-penetration':           '10',
    '%resistance-penetration':      '11',
    '%dodge-chance':                '12',
    '%deflection-chance':           '13',
    '%physical-critical-chance':    '14',
    '%special-critical-chance':     '15',
    '%critical-damage':             '16',
    '%potency':                     '17',
    '%tenacity':                    '18',
    '%health-steal':                '27',
    '%protection':                  '28',
    '%physical-accuracy':           '37',
    '%special-accuracy':            '38',
    '%physical-critical-avoidance': '39',
    '%special-critical-avoidance':  '40',
}

def now(timezone):
	tz = pytz.timezone(timezone)
	return tz.localize(datetime.now())

def basicstrip(string):
	return string.replace(' ', '').replace('"', '').replace('(', '').replace(')', '').lower()

def format_char_details(unit, fmt):

	for pattern, json_key in FORMAT_LUT.items():
		if pattern in fmt:
			fmt = fmt.replace(pattern, str(unit[json_key]))

	return fmt

def format_char_stats(unit, fmt):

	stats = unit['stats']

	for pattern, key in STATS_LUT.items():

		if pattern in fmt:

			data = stats[key]
			if pattern in [ '%critical-damage', '%potency', '%tenacity' ]:
				data = 100 * data

			data = round(data)

			if pattern in PERCENT_STATS:
				data = '%d%%' % data

			fmt = fmt.replace(pattern, str(data)).replace('%20', ' ').replace('%0a', '\n').replace('%0A', '\n')

	return fmt

def update_source_code():
	subprocess.call([ 'git', 'fetch'])
	subprocess.call([ 'git', 'pull' ])

def exit_bot():
	# TODO send message on quit, like animated an
	# gif of an explosion or something like that.
	from ipd import bot
	bot.logout()
	bot.close()
	print('Restarting!')
	sys.exit()

def ensure_parents(filepath):
	os.makedirs(os.path.dirname(filepath), exist_ok=True)
