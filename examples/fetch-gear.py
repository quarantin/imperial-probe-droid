#!/usr/bin/python3

import json, os, requests

from swgohgg import get_gear_list

all_gear = get_gear_list()

for gear_id, gear in all_gear.items():
	url = gear['image'].replace('//', 'https://', 1)
	print('Fetching %s' % url)
	response = requests.get(url)
	if response.status_code == 200:
		basename = os.path.basename(url)
		save_path = 'django/images/assets/%s' % basename
		with open(save_path, 'wb') as fout:
			for chunk in response:
				fout.write(chunk)
	else:
		print('ERROR: Failed fetching %s' % url)
