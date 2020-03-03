from django.shortcuts import render
from django.http import JsonResponse 

from .models import *

def login_success(request):

	google_code = 'No access token specified.'

	if request.method == 'GET':

		google_code = 'No access token specified (GET).'
		if 'code' in request.GET:
			google_code = request.GET['code']

	return google_code
