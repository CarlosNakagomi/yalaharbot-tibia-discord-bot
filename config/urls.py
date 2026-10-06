from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from bot.views import (
    DiscordUserViewSet,
    CharacterViewSet,
    CharacterDeathViewSet,
    DiscordServerSettingsViewSet,
    DiscordUserAndCharactersViewSet,
    WatchedGuildViewSet,
    WatchedWorldViewSet,
    next_app,
    EnemyGuildViewSet,
    EnemyListConfigurationView,
    EnemyStatusView,
    EnemyObservationView,
    CombinedMonitorStatusView,
    HealthView,
    SiteAccessStatusView,
    SiteAccessLoginView,
    SiteAccessLogoutView,
)

router = DefaultRouter()
router.register(r'api/discord-users', DiscordUserViewSet)
router.register(r'api/characters', CharacterViewSet)
router.register(r'api/character-deaths', CharacterDeathViewSet)
router.register(r'api/server-settings', DiscordServerSettingsViewSet)
router.register(r'api/discord-user-characters', DiscordUserAndCharactersViewSet)
router.register(r'api/watched-guilds', WatchedGuildViewSet)
router.register(r'api/watched-worlds', WatchedWorldViewSet)
router.register(r'api/enemy-guilds', EnemyGuildViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthView.as_view()),
    path('api/site-access/status/', SiteAccessStatusView.as_view()),
    path('api/site-access/login/', SiteAccessLoginView.as_view()),
    path('api/site-access/logout/', SiteAccessLogoutView.as_view()),
    path('api/enemy-list/config/', EnemyListConfigurationView.as_view()),
    path('api/enemy-list/status/', EnemyStatusView.as_view()),
    path('api/enemy-list/observations/', EnemyObservationView.as_view()),
    path('api/monitors/status/', CombinedMonitorStatusView.as_view()),
    path('', include(router.urls)),  # Servir las rutas de la API en la raíz.
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    frontend_out = settings.BASE_DIR / 'frontend' / 'out'
    if frontend_out.exists():
        urlpatterns += static(settings.STATIC_URL, document_root=frontend_out)

urlpatterns += [
    re_path(r'^(?P<path>.*)$', next_app, name='next_app'),
]
