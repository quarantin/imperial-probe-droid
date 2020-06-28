"""swgoh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
	path('', views.index),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path('dashboard/', views.dashboard),
	path('profile/', views.UserDetailView.as_view()),
	path('settings/', views.PlayerUpdateView.as_view()),
	path('guild/tickets/guild-daily/json/', views.guild_tickets_guild_daily_json),
	path('guild/tickets/guild-daily/', views.guild_tickets_guild_daily),
	path('guild/tickets/total-per-user/json/', views.guild_tickets_total_per_user_json),
	path('guild/tickets/total-per-user/', views.guild_tickets_total_per_user),
	path('guild/tickets/detail/json/', views.guild_tickets_detail_json),
	path('guild/tickets/detail/', views.guild_tickets_detail),
	path('guild/tickets/average/', views.GuildTicketsAveragePerUser.as_view()),
	path('guild/', views.guild),
	path('ga/', include('grandarena.urls')),
	path('grand-arena/', include('grandarena.urls')),
	path('tb/', include('territorybattle.urls')),
	path('territory-battle/', include('territorybattle.urls')),
	path('tw/', include('territorywar.urls')),
	path('territory-war/', include('territorywar.urls')),
	path('avatar/<str:base_id>', views.avatar),
	path('gear/<str:base_id>/', views.gear),
	path('relic/<int:relic>/<str:align>/', views.relic),
	path('skill/<str:skill_id>/', views.skill),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
