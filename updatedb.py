#!/usr/bin/env python3

import asyncio

import client
import libswgoh

import DJANGO

from swgoh.models import Player

async def main():

	players = {}

	session = await libswgoh.get_auth_guest()

	for player in Player.objects.all():

		if player.ally_code in players:
			print('duplicate allycode: %s' % player.ally_code)
			continue

		players[player.ally_code] = True
		profile = await client.get_player_profile(ally_code=str(player.ally_code), session=session)
		if not profile:
			print('failed retrieving profile for: %s' % player.ally_code)
			continue

		print('Saving player ID %s for %s' % (profile['id'], profile['name']))
		player.player_id = profile['id']
		player.save()

	await libswgoh.do_logout(session=session)

if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(main())
