# -*- coding: utf-8 -*-

import math
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.http import FileResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cairosvg import svg2png

import io, os, requests

from .models import Gear, BaseUnit, BaseUnitSkill, Player, WebUser

def index(request):

	ctx = {}

	ctx['github_url'] = 'https://github.com/quarantin/imperial-probe-droid'
	ctx['patreon_url'] = 'https://www.patreon.com/imperial_probe_droid'
	ctx['image_path'] = '/media/ipd-coming-soon.gif'

	return render(request, 'swgoh/index.html', ctx)

@login_required
def dashboard(request):

	ctx = {}
	return render(request, 'swgoh/dashboard.html', ctx)

class WebUserDetailView(DetailView):

	model = WebUser

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		return context

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super().dispatch(*args, **kwargs)

	def get(self, request, *args, **kwargs):

		self.object = WebUser.objects.get(user=request.user)

		context = self.get_context_data(*args, **kwargs)

		return self.render_to_response(context)

class PlayerUpdateView(UpdateView):

	model = Player
	fields = [ 'ally_code', 'language', 'timezone' ]
	template_name_suffix = '_update_form'
	success_url = '/settings/'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super().dispatch(*args, **kwargs)

	def get_object(self):
		user = get_object_or_404(User, pk=self.request.user.id)
		webuser = get_object_or_404(WebUser, user=user)
		return webuser.player

	def get_success_url(self):
		messages.success(self.request, 'Settings updated successfully.')
		return self.success_url

@login_required
def guild(request):
	ctx = {}
	return render(request, 'swgoh/guild.html', ctx)

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

	image = get_relic(relic, align, raw=True)
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
	width, height = 256, 256
	image = Image.new('RGBA', (256, 256))
	portrait = Image.open(download_image(character)).convert('RGBA')

	x = int(width / 2 + image.width / 2)
	y = int(height / 2 + image.height / 2)
	image.paste(portrait, (x, y), portrait)
	image.show()
	return image

def get_gear(gear, alignment):

	if gear is None:
		return None

	align = gear >= 13 and '-%s-side' % alignment or ''
	image_name = 'gear-%02d%s.png' % (gear, align)
	image_path = download_image(image_name)
	return Image.open(image_path)

def get_level(level):

	if not level:
		return None

	offset = 0
	if level < 10:
		offset = 5

	image_name = 'level.png'
	image_path = download_image(image_name)

	level_image = Image.open(image_path)
	draw = ImageDraw.Draw(level_image)
	font = ImageFont.truetype('fonts/arial.ttf', 24)
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

	rarity_img = Image.new('RGBA', (star_img.width * 7, star_img.height), 0)

	for i in range(0, rarity):
		rarity_img.paste(star_img, (i * 17, 0), star_img)

	for i in range(rarity, 7):
		rarity_img.paste(no_star_img, (i * 17, 0), no_star_img)

	return rarity_img

def get_zetas(zetas):

	image_name = 'zeta-48x48.png'
	image_path = download_image(image_name)

	zeta_image = Image.open(image_path)
	draw = ImageDraw.Draw(zeta_image)
	font = ImageFont.truetype('fonts/arialbd.ttf', 14)
	draw.text((20, 12), '%d' % zetas, (255, 255, 255), font=font)
	return zeta_image

def get_relic(relic, alignment, raw=False):

	final_path = 'images/relic-%s-side-%d.png' % (alignment, relic)
	if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
		return raw is False and Image.open(final_path) or file_content(final_path)

	image_name = 'relic-%s-side.png' % alignment
	image_path = download_image(image_name)

	relic_image = Image.open(image_path)
	draw = ImageDraw.Draw(relic_image)
	font = ImageFont.truetype('fonts/arialbd.ttf', 14)

	x = 23
	y = 19

	draw.text((x + 1, y + 1), '%d' % relic, font=font, fill='black')
	draw.text((x + 2, y + 1), '%d' % relic, font=font, fill='black')
	draw.text((x, y), '%d' % relic, font=font, fill='white')

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

def get_param(request, param, default=0):

	try:
		return param in request.GET and request.GET[param] and type(default)(request.GET[param]) or default
	except:
		return default

def has_params(request):
	for param in [ 'level', 'gear', 'rarity', 'zetas', 'relic' ]:
		if param in request.GET and int(request.GET[param]):
			return True
	return False

def get_avatar(request, base_id):

	alignment = get_param(request, 'alignment', 'neutral').lower()
	gear      = get_param(request, 'gear')
	level     = get_param(request, 'level')
	rarity    = get_param(request, 'rarity')
	zeta      = get_param(request, 'zetas')
	relic     = get_param(request, 'relic')

	gear_str   = 'G%d' % gear
	level_str  = 'L%d' % level
	rarity_str = 'S%d' % rarity
	zeta_str   = 'Z%d' % zeta
	relic_str  = 'R%d' % relic

	filename = './images/%s.png' % '_'.join([ base_id, alignment, gear_str, level_str, rarity_str, zeta_str, relic_str ])
	if os.path.exists(filename):
		return filename, Image.open(filename)

	width, height = 256, 256
	size = (width, height)
	radius = int(width / 4)
	image = Image.new('RGBA', (width, height))

	portrait_path = download_image(base_id)
	portrait = Image.open(portrait_path).convert('RGBA')
	portrait.thumbnail((128, 128), Image.ANTIALIAS)

	portrait_x = int(image.width  / 2 - portrait.width  / 2)
	portrait_y = int(image.height / 2 - portrait.height / 2)

	image.paste(portrait, (portrait_x, portrait_y), portrait)

	if has_params(request):
		mask = Image.new('L', size, 0)
		draw = ImageDraw.Draw(mask)
		circle = [ (radius, radius), (radius * 3, radius * 3) ]
		draw.ellipse(circle, fill=255)

		image = ImageOps.fit(image, size)
		image.putalpha(mask)

	if alignment not in ALIGNMENTS:
		alignment = 'neutral'

	if gear > 0:
		gear_image   = get_gear(gear, alignment)
		gear_x = int(image.width  / 2 - gear_image.width / 2)
		gear_y = int(image.height / 2 - gear_image.height / 2)
		image.paste(gear_image, (gear_x, gear_y), gear_image)

	if level > 0:
		level_image  = get_level(level)
		level_x = int(image.width / 2 - level_image.width / 2)
		level_y = int(image.height / 2 - level_image.height / 2 + 10)
		image.paste(level_image, (level_x, level_y), level_image)

	if rarity > 0:
		rarity_image = get_rarity(rarity)
		rarity_x = int(image.width / 2 - portrait.width / 2 + rarity_image.height / 4)
		rarity_y = int(image.height / 2 - portrait.height / 2 - rarity_image.height)
		image.paste(rarity_image, (rarity_x, rarity_y), rarity_image)

	if zeta > 0:
		zeta_image   = get_zetas(zeta)
		zeta_x = int(image.width / 4 - 10)
		zeta_y = int(image.height / 2 + zeta_image.height / 4 + 5)
		image.paste(zeta_image, (zeta_x, zeta_y), zeta_image)

	if relic > 0:
		relic_image  = get_relic(relic, alignment)
		relic_x = int(image.width / 2 + relic_image.width / 4 + 5)
		relic_y = int(image.height / 2 + relic_image.height / 4 - 3)
		image.paste(relic_image, (relic_x, relic_y), relic_image)

	image = image.crop((radius - 10, radius - 20, radius * 3 + 10, radius * 3 + 10))

	image.save(filename, format='PNG')

	return filename, image

def avatar(request, base_id):
	filename, image = get_avatar(request, base_id)
	return FileResponse(open(filename, 'rb'))
