from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from bot.views import DiscordUserViewSet, CharacterViewSet, DiscordUserAndCharactersViewSet, index

router = DefaultRouter()
router.register(r'api/discord-users', DiscordUserViewSet)
router.register(r'api/characters', CharacterViewSet)
router.register(r'api/discord-user-characters', DiscordUserAndCharactersViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),  # Servir las rutas de la API en la raíz.
    re_path(r'^.*', index, name='index'),  # Manejar las rutas de React.
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('/static/frontend/', document_root=settings.BASE_DIR / 'frontend' / 'build' / 'static')
