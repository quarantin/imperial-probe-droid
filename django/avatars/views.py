#!/usr/bin/python3
# -*- coding: utf-8 -*-

from django.http import HttpResponse

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cairosvg import svg2png

import io, os, requests


def download_image(image_name):

	IMAGES = './images/'
	image_path = '%s%s' % (IMAGES, image_name)

	if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:

		url = 'https://swgoh.gg/static/img/%s' % image_name

		response = requests.get(url)
		image_data = response.content

		fin = open(image_path, 'wb+')
		fin.write(image_data)
		fin.close()

	return image_path

def get_portrait(character):

	image_name = 'assets/%s' % character
	image_path = download_image(image_name)

	return Image.open(image_path)

def get_gear(gear):

	image_name = 'ui/gear-icon-g%d.svg' % gear
	image_path = download_image(image_name)
	image_png = image_path.replace('.svg', '.png')

	if not os.path.exists(image_png) or os.path.getsize(image_png) == 0:
		svg2png(url=image_path, write_to=image_png, parent_width=128, parent_height=128)

	return Image.open(image_png)

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
	pass

def get_zetas(zetas):

	image_name = 'zeta.png'
	image_path = download_image(image_name)

	zeta_image = Image.open(image_path)
	draw = ImageDraw.Draw(zeta_image)
	font = ImageFont.truetype('arial.ttf', 16)
	draw.text((27, 18), '%d' % zetas, (255, 255, 255), font=font)
	return zeta_image

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

def avatar(request, character, level, gear, rarity, zetas):

	portrait_image = get_portrait(character)
	level_image = get_level(level)
	gear_image = get_gear(gear)
	rarity_image = get_rarity(rarity)

	portrait_image.paste(gear_image, (0, 0), gear_image)
	portrait_image = format_image(portrait_image, 128)

	full_image = Image.new('RGBA', (138, 138), 0)
	full_image.paste(portrait_image, (5, 5), portrait_image)
	if zetas > 0:
		zeta_image = get_zetas(zetas)
		full_image.paste(zeta_image, (-8, 63), zeta_image)
	full_image.paste(level_image, (5, 10), level_image)

	full_image = format_image(full_image, 138)

	return HttpResponse(img2png(full_image), content_type='image/png')
