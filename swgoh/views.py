import os

from django.http import HttpResponse

from .models import Gear

def download(gear):

	image_path = 'images/gear-%s.png' % gear.id

	if not os.path.exists(image_path):

		url = 'https://swgoh.gg%s' % gear.url

		response = requests.get(url)
		response.raise_for_status()

		fout = open(image_path, 'wb')
		fout.write(response.content)
		fout.close()

	return image_path

def gear(request, gear):

	try:
		image_path = download(Gear.objects.get(base_id=gear))
		fin = open(image_path, 'r')
		data = fin.read()
		fin.close()
		return HttpResponse(content_type='image/png')

	except Gear.DoesNotExist:
		raise Http404('Could not find gear: %s' % gear)


def login_success(request):

	google_code = 'No access token specified.'

	if request.method == 'GET':

		google_code = 'No access token specified (GET).'
		if 'code' in request.GET:
			google_code = request.GET['code']

	return HttpResponse(google_code)
