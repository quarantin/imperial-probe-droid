# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404


from PIL import Image, ImageDraw, ImageFont, ImageOps

from cairosvg import svg2png

import io, os, requests

ALIGNMENTS = {
	'dark': True,
	'light': True,
	'neutral': True,
}

def download_image(image_name):

	image_path = './images/%s' % image_name
	if not image_path.endswith('.png'):
		image_path = '%s.png' % image_path

	if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:

		url = 'https://swgoh.gg/game-asset/u/%s/' % image_name

		response = requests.get(url)
		if response.status_code == 404:
			raise Http404('Could not find character: %s' % image_name)

		response.raise_for_status():

		image_data = response.content

		fin = open(image_path, 'wb+')
		fin.write(image_data)
		fin.close()

	return image_path

def get_portrait(character):
	return Image.open(download_image(character))

def get_gear(gear, alignment):

	if gear < 13:
		image_name = 'gear-%02d.png' % gear
	else:
		image_name = 'gear-%d-%s-side.png' % (gear, alignment)

	image_path = download_image(image_name)
	return Image.open(image_path)

def get_level(level):

	offset = 0
	if level < 10:
		offset = 5

	image_name = 'level.png'
	image_path = download_image(image_name)

	level_image = Image.open(image_path)
	draw = ImageDraw.Draw(level_image)
	font = ImageFont.truetype('arial.ttf', 24)
	draw.text((51 + offset, 93), "%d" % level, (255, 255, 255), font=font)
	return level_image

def get_rarity(rarity):

	star_image_name = 'star.png'
	star_image_path = download_image(star_image_name)

	no_star_image_name = 'star-inactive.png'
	no_star_image_path = download_image(no_star_image_name)

	star_img = Image.open(star_image_path)
	no_star_img = Image.open(no_star_image_path)

	rarity_img = Image.new('RGBA', (154, 22), 0)

	for i in range(0, rarity):
		rarity_img.paste(star_img, (i * 20 - 2, 0), star_img)

	for i in range(rarity, 7):
		rarity_img.paste(no_star_img, (i * 20 - 2, 0), no_star_img)

	return rarity_img

def get_zetas(zetas):

	image_name = 'zeta.png'
	image_path = download_image(image_name)

	zeta_image = Image.open(image_path)
	draw = ImageDraw.Draw(zeta_image)
	font = ImageFont.truetype('arial.ttf', 16)
	draw.text((27, 18), '%d' % zetas, (255, 255, 255), font=font)
	return zeta_image

def get_relics(relics, alignment):

	image_name = 'relic-%s-side.png' % alignment
	image_path = download_image(image_name)

	relic_image = Image.open(image_path)
	draw = ImageDraw.Draw(relic_image)
	font = ImageFont.truetype('arial.ttf', 16)
	draw.text((22, 18), '%d' % relics, (255, 255, 255), font=font)
	return relic_image

def format_image(image, radius):
	size = (radius, radius)
	mask = Image.new('L', size, 0)
	draw = ImageDraw.Draw(mask)
	draw.ellipse((0, 0) + size, fill=255)
	data = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
	data.putalpha(mask)
	return data

def img2png(image):

	with io.BytesIO() as output:
		image.save(output, format='PNG')
		return output.getvalue()

	return None

def get_avatar(request, portrait):

	alignment  = 'alignment' in request.GET and request.GET['alignment'] and request.GET['alignment'].lower() in ALIGNMENTS and request.GET['alignment'].lower() or 'neutral'
	level = 'level' in request.GET and int(request.GET['level']) or 1
	gear = 'gear' in request.GET and int(request.GET['gear']) or 1
	rarity = 'rarity' in request.GET and int(request.GET['rarity']) or 0
	zetas = 'zetas' in request.GET and int(request.GET['zetas']) or 0
	relics = 'relics' in request.GET and int(request.GET['relics']) or 0

	portrait_image = get_portrait(portrait)
	level_image = get_level(level)
	gear_image = get_gear(gear, alignment)
	rarity_image = get_rarity(rarity)
	zeta_image = get_zetas(zetas)
	relic_image = get_relics(relics, alignment)

	if gear < 13:
		portrait_image.paste(gear_image, (0, 0), gear_image)
	else:
		portrait_image.paste(gear_image, (-15, -11), gear_image)

	portrait_image = format_image(portrait_image, 128)

	full_image = Image.new('RGBA', (138, 138), 0)
	full_image.paste(portrait_image, (5, 5), portrait_image)

	full_image = format_image(full_image, 138)

	if zetas > 0:
		full_image.paste(zeta_image, (-8, 63), zeta_image)
	if relics > 0:
		full_image.paste(relic_image, (75, 63), relic_image)
	full_image.paste(level_image, (5, 10), level_image)
	full_image.paste(rarity_image, (0, 0), rarity_image)

	return full_image

def avatar(request, portrait):
	return HttpResponse(img2png(get_avatar(request, portrait)), content_type='image/png')

def stats(request, portrait, ally_code):


	full_image = Image.open('./images/background.png')

	avatar = get_avatar(request, portrait)

	full_image.paste(avatar, (10, 10), avatar)

	draw = ImageDraw.Draw(full_image)
	font = ImageFont.truetype('arial.ttf', 16)

	x = 150
	y = 20

	for key in request.GET:
		string = '%s:' % key.title()
		draw.text((x, y), string, (255, 255, 255), font=font)
		y += 20

	x = 250
	y = 20

	for key, val in request.GET.items():
		draw.text((x, y), val, (255, 255, 255), font=font)
		y += 20

	return HttpResponse(img2png(full_image), content_type='image/png')
