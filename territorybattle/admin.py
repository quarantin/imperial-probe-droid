from django.contrib import admin

from .models import TerritoryBattleHistory

class TerritoryBattleHistoryAdmin(admin.ModelAdmin):
	pass

admin.site.register(TerritoryBattleHistory, TerritoryBattleHistoryAdmin)
