import requests

from datetime import datetime, timedelta

cache = {}

def expired(date):
	return datetime.now() > date + timedelta(hours=1)

def download(url): 
	if url in cache and not expired(cache[url]['updated']):
		print('Fetching %s from cache' % url)
		return cache[url]['json'], True

	print('Downloading %s' % url)
	response = requests.get(url)
	if response.status_code != 200:
		raise Exception('Failed to request %s' % url)

	cache[url] = {
		'json': response.json(),
		'updated': datetime.now(),
	}

	return cache[url]['json'], False
