#!/usr/bin/env python3

import os
import sys
import json
import gzip
import asyncio
from datetime import datetime

import DJANGO
from territorybattle.models import TerritoryBattle, TerritoryBattleHistory

from libswgoh import fix_json_events

import protos.swgoh_pb2 as swgoh
import protos.ChannelRpc_pb2 as ChannelRpc

def datetime_converter(o):
	if isinstance(o, datetime):
		return o.strftime('%Y-%M-%D %H:%M:%S')

def parse_raw(filename):

	print('Parsing %s' % filename)

	fin = open(filename, 'rb')
	data = fin.read()
	fin.close()

	response = swgoh.ResponseEnvelope()
	response.ParseFromString(data)
	if response.code != swgoh.ResponseCode.Value('OK'):
		print(response)
		raise Exception(response)

	payload = gzip.decompress(response.payload)

	event_response = ChannelRpc.GetEventsResponse()
	event_response.ParseFromString(payload)

	events = fix_json_events(event_response)
	for event in events:

		if 'id' not in event or not event['id']:
			print('Skipping event with no id:')
			#print(json.dumps(event, indent=4, default=datetime_converter))
			continue

		print('Parsing event %s' % event['id'])

		try:
			db_event = TerritoryBattleHistory.objects.get(id=event['id'])

		except TerritoryBattleHistory.DoesNotExist:

			if 'event_id' not in event or not event['event_id'].startswith('TB_EVENT_'):
				#print('Skipping event with no event_id:')
				#print(json.dumps(event, indent=4, default=datetime_converter))
				continue

			event['tb'] = TerritoryBattle.parse(event.pop('event_id'))

			db_event = TerritoryBattleHistory(**event)
			db_event.save()


async def parse(client, creds_id='anraeth'):

	event_id = 'TB_EVENT_GEONOSIS_SEPARATIST:O1588352400000'
	events = await client.get_tb_events(creds_id=creds_id, event_id=event_id)

	for event in events:

		try:
			db_event = TerritoryBattleHistory.objects.get(id=event['id'])

		except TerritoryBattleHistory.DoesNotExist:

			event['tb'] = TerritoryBattle.parse(event.pop('event_id'))

			db_event = TerritoryBattleHistory(**event)
			db_event.save()


if __name__ == '__main__':

	tbs = [
		'TB_EVENT_GEONOSIS_REPUBLIC:O1584550800000',
		'TB_EVENT_GEONOSIS_REPUBLIC:O1587056400000',
		'TB_EVENT_GEONOSIS_SEPARATIST:O1583172000000',
		'TB_EVENT_GEONOSIS_SEPARATIST:O1585760400000',
		'TB_EVENT_GEONOSIS_SEPARATIST:O1588352400000',
		'TB_EVENT_HOTH_EMPIRE:O1580580000000',
		'TB_EVENT_HOTH_EMPIRE:O1583172000000',
		'TB_EVENT_HOTH_EMPIRE:O1588352400000',
		'TB_EVENT_HOTH_REBEL:O1581876000000',
		'TB_EVENT_HOTH_REBEL:O1584550800000',
		'TB_EVENT_HOTH_REBEL:O1587056400000',
	]


	if len(sys.argv) < 2:
		from client import SwgohClient
		asyncio.get_event_loop().run_until_complete(parse(SwgohClient()))
		sys.exit(0)


	source = sys.argv[1]
	with open(source, 'r') as fin:
		for filename in fin:
			filename = filename.strip()
			if os.path.exists(filename):
				parse_raw(filename)
			else:
				print('Skipping missing file: %s' % filename)
