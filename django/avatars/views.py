#!/usr/bin/python3
# -*- coding: utf-8 -*-

from django.http import HttpResponse

from PIL import Image, ImageDraw, ImageOps

from cairosvg import svg2png

import io, os, requests

IMAGES = './images/'

def download_image(image_name):

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
	pass

def get_rarity(rarity):
	pass

def format_image(image):

	size = (128, 128)
	mask = Image.new('L', size, 0)
	draw = ImageDraw.Draw(mask)
	draw.ellipse((0, 0) + size, fill=255)
	data = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
	data.putalpha(mask)

	with io.BytesIO() as output:
		data.save(output, format='PNG')
		return output.getvalue()

	return None

def avatar(request, character, level, gear, rarity):

	portrait_image = get_portrait(character)
	level_image = get_level(level)
	gear_image = get_gear(gear)
	rarity_image = get_rarity(rarity)

	portrait_image.paste(gear_image, (0, 0), gear_image)

	return HttpResponse(format_image(portrait_image), content_type='image/png')
