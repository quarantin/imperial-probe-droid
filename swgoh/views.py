# -*- coding: utf-8 -*-

import math
from django.http import HttpResponse, Http404

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cairosvg import svg2png

import io, os, requests

from .models import Gear, BaseUnitSkill

def file_content(path):
	fin = open(path, 'rb')
	data = fin.read()
	fin.close()
	return data

background_colors = {
	 1: ( 67, 145, 163),
	 2: ( 76, 150,   1),
	 4: (  0,  75, 101),
	 7: ( 71,   0, 167),
	 9: ( 71,   0, 167),
	11: ( 71,   0, 167),
	12: (153, 115,   0),
}

def get_gear_background(gear, size):

	width, height = size
	image = Image.new('RGBA', (width, height))
	center = background_colors[gear.tier]
	border = (0, 0, 0)

	for y in range(height):
		for x in range(width):
			distanceToCenter = math.sqrt((x - width / 2) ** 2 + (y - height / 2) ** 2)
			distanceToCenter = float(distanceToCenter) / (math.sqrt(2) * width / 2)
			r = int(border[0] * distanceToCenter + center[0] * (1 - distanceToCenter))
			g = int(border[1] * distanceToCenter + center[1] * (1 - distanceToCenter))
			b = int(border[2] * distanceToCenter + center[2] * (1 - distanceToCenter))

			image.putpixel((x, y), (r, g, b))

	return image

def crop_corners(image):

	image_size = 128

	triangle_1_size = 15
	triangle_1 = [
		(0, 0),
		(0, triangle_1_size),
		(triangle_1_size, 0),
	]

	triangle_2_size = 16
	triangle_2 = [
		(image_size, image_size),
		(image_size, image_size - triangle_2_size),
		(image_size - triangle_2_size, image_size),
	]

	triangle_3_size = 8
	triangle_3 = [
		(0, image_size),
		(0, image_size - triangle_3_size),
		(triangle_3_size, image_size),
	]

	draw = ImageDraw.Draw(image)

	draw.polygon(triangle_1, fill=255)
	draw.polygon(triangle_2, fill=255)
	draw.polygon(triangle_3, fill=255)

	return image

def download_gear(gear):

	image_path = 'images/equip-%s.png' % gear.base_id

	if not os.path.exists(image_path):

		url = 'https://swgoh.gg%s' % gear.image

		response = requests.get(url)
		response.raise_for_status()

		fout = open(image_path, 'wb')
		fout.write(response.content)
		fout.close()

	return image_path

def download_skill(skill):

	image_path = 'images/skill.%s.png' % skill.skill_id

	if not os.path.exists(image_path):

		url = 'https://swgoh.gg/game-asset/a/%s/' % skill.skill_id

		response = requests.get(url)
		response.raise_for_status()

		fout = open(image_path, 'wb')
		fout.write(response.content)
		fout.close()

	return image_path

def get_gear_portrait(gear):

	final_path = 'images/equip-%s-tier-%02d.png' % (gear.base_id, gear.tier)
	if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
		return file_content(final_path)

	gear_path = download_gear(gear)
	gear_image = Image.open(gear_path)

	border_path = 'images/border-tier-%02d.png' % gear.tier
	border_image = Image.open(border_path)

	image = get_gear_background(gear, gear_image.size)
	image.paste(gear_image, (0, 0), gear_image)
	image.paste(border_image, (0, 0), border_image)

	crop_corners(image).save(final_path)
	return file_content(final_path)

def gear(request, base_id):

	try:
		gear = Gear.objects.get(base_id=base_id)
		image = get_gear_portrait(gear)
		return HttpResponse(image, content_type='image/png')

	except Gear.DoesNotExist:
		raise Http404('Could not find gear: %s' % base_id)

def relic(request, relic, align):

	image = get_relics(relic, align, raw=True)
	return HttpResponse(image, content_type='image/png')

def skill(request, skill_id):

	try:
		skill = BaseUnitSkill.objects.get(skill_id=skill_id)
		skill_path = download_skill(skill)
		image = file_content(skill_path)
		return HttpResponse(image, content_type='image/png')

	except BaseUnitSkill.DoesNotExist:
		raise Http404('Could not find skill: %s' % skill_id)

def login_success(request):

	google_code = 'No access token specified.'

	if request.method == 'GET':

		google_code = 'No access token specified (GET).'
		if 'code' in request.GET:
			google_code = request.GET['code']

	return HttpResponse(google_code)

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

		response.raise_for_status()

		image_data = response.content

		fin = open(image_path, 'wb+')
		fin.write(image_data)
		fin.close()

	return image_path

def get_portrait(character):
	return Image.open(download_image(character)).convert('RGBA')

def get_gear(gear, alignment):

	if gear is None:
		return None

	align = gear >= 13 and '-%s-side' % alignment or ''
	image_name = 'gear-%02d%s.png' % (gear, align)
	image_path = download_image(image_name)
	return Image.open(image_path)

def get_level(level):

	if level is None:
		return None

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

	if rarity is None:
		return None

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

def get_relics(relics, alignment, raw=False):

	final_path = 'images/relic-%s-side-%d.png' % (alignment, relics)
	if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
		return raw is False and Image.open(final_path) or file_content(final_path)

	image_name = 'relic-%s-side.png' % alignment
	image_path = download_image(image_name)

	relic_image = Image.open(image_path)
	draw = ImageDraw.Draw(relic_image)
	font = ImageFont.truetype('arial.ttf', 16)
	draw.text((23, 18), '%d' % relics, (255, 255, 255), font=font)

	relic_image.save(final_path)
	return raw is False and relic_image or file_content(final_path)

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
	level = 'level' in request.GET and int(request.GET['level']) or None
	gear = 'gear' in request.GET and int(request.GET['gear']) or None
	rarity = 'rarity' in request.GET and int(request.GET['rarity']) or None
	zetas = 'zetas' in request.GET and int(request.GET['zetas']) or 0
	relics = 'relics' in request.GET and int(request.GET['relics']) or 0

	do_circle = level or gear or rarity or zetas or relics

	portrait_image = get_portrait(portrait)
	level_image = get_level(level)
	gear_image = get_gear(gear, alignment)
	rarity_image = get_rarity(rarity)
	zeta_image = get_zetas(zetas)
	relic_image = get_relics(relics, alignment)

	if gear_image is not None:
		dims = gear >= 13 and (-15, -11) or (0, 0)
		portrait_image.paste(gear_image, dims, gear_image)

	if do_circle:
		portrait_image = format_image(portrait_image, 128)

	full_image = Image.new('RGBA', (138, 138), 0)
	full_image.paste(portrait_image, (5, 5), portrait_image)

	if do_circle:
		full_image = format_image(full_image, 138)

	if zetas > 0:
		full_image.paste(zeta_image, (-8, 63), zeta_image)
	if relics > 0:
		full_image.paste(relic_image, (75, 63), relic_image)
	if level_image is not None:
		full_image.paste(level_image, (5, 10), level_image)
	if rarity_image is not None:
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
