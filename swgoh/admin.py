from django.contrib import admin

from .models import Player

class PlayerAdmin(admin.ModelAdmin):
	list_display = [ f.name for f in Player._meta.fields if f.name != 'id' ]

admin.site.register(Player, PlayerAdmin)
