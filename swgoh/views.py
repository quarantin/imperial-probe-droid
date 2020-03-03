from django.http import HttpResponse

def login_success(request):

	google_code = 'No access token specified.'

	if request.method == 'GET':

		google_code = 'No access token specified (GET).'
		if 'code' in request.GET:
			google_code = request.GET['code']

	return HttpResponse(google_code)
