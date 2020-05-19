from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

class CustomUserAdmin(UserAdmin):
	#fieldsets = UserAdmin.fieldsets#
	fieldsets = (
		('SWGOH', {
			'fields': ('player', 'guild', 'discord_id', 'creds_id', 'premium_type'),
		}),
	) + UserAdmin.fieldsets

admin.site.register(User, CustomUserAdmin)
