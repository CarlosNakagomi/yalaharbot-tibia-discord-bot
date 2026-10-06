from rest_framework import viewsets, status
from .models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
    EnemyGuild,
    EnemyListConfiguration,
    EnemyObservation,
)
from .serializers import (
    DiscordUserSerializer,
    CharacterSerializer,
    CharacterDeathSerializer,
    DiscordServerSettingsSerializer,
    DiscordUserAndCharactersSerializer,
    WatchedGuildSerializer,
    WatchedWorldSerializer,
    EnemyGuildSerializer,
    EnemyListConfigurationSerializer,
    EnemyObservationSerializer,
)
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from rest_framework.decorators import action
from pathlib import PurePosixPath
import tibiapy
from tibiapy.parsers import CharacterParser
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from .utils import get_online_enemies, get_monitored_statuses, track_enemy_online_sessions
from django.conf import settings
from secrets import compare_digest
from django.core import signing
from .site_access import COOKIE_SALT


class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer

    @action(detail=False, methods=['get'])
    def fetch_tibia_data(self, request):
        name = request.query_params.get('name')
        if not name:
            return Response({'error': 'Character name is required'}, status=status.HTTP_400_BAD_REQUEST)

        url = tibiapy.urls.get_character_url(name)
        r = requests.get(url)
        content = r.text
        character = CharacterParser.from_content(content)

        if character is None:
            return Response({'error': 'Character not found'}, status=status.HTTP_404_NOT_FOUND)

  # Extraer solo los nombres de los personajes
        other_characters_names = [other_char.name for other_char in character.other_characters]

        data = {
            'name': character.name,
            'level': character.level,
            'vocation': str(character.vocation),
            'world': character.world,
            'last_login': str(character.last_login),
            'other_characters': other_characters_names,
        }

        return Response(data)

class DiscordUserViewSet(viewsets.ModelViewSet):
    queryset = DiscordUser.objects.all()
    serializer_class = DiscordUserSerializer



class DiscordUserAndCharactersViewSet(viewsets.ModelViewSet):
    queryset = DiscordUserAndCharacters.objects.all()
    serializer_class = DiscordUserAndCharactersSerializer


class CharacterDeathViewSet(viewsets.ModelViewSet):
    queryset = CharacterDeath.objects.select_related('character').all()
    serializer_class = CharacterDeathSerializer


class DiscordServerSettingsViewSet(viewsets.ModelViewSet):
    queryset = DiscordServerSettings.objects.all()
    serializer_class = DiscordServerSettingsSerializer


class WatchedWorldViewSet(viewsets.ModelViewSet):
    queryset = WatchedWorld.objects.select_related('settings').all()
    serializer_class = WatchedWorldSerializer


class WatchedGuildViewSet(viewsets.ModelViewSet):
    queryset = WatchedGuild.objects.select_related('settings').all()
    serializer_class = WatchedGuildSerializer


class EnemyGuildViewSet(viewsets.ModelViewSet):
    queryset = EnemyGuild.objects.all()
    serializer_class = EnemyGuildSerializer


class EnemyListConfigurationView(APIView):
    def get_object(self):
        configuration, _ = EnemyListConfiguration.objects.get_or_create(pk=1)
        return configuration

    def get(self, request):
        return Response(EnemyListConfigurationSerializer(self.get_object()).data)

    def put(self, request):
        serializer = EnemyListConfigurationSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        serializer = EnemyListConfigurationSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EnemyStatusView(APIView):
    def get(self, request):
        configuration, _ = EnemyListConfiguration.objects.get_or_create(pk=1)
        if not configuration.selected_world:
            return Response({'error': 'Configure a Tibia world first.'}, status=status.HTTP_400_BAD_REQUEST)

        guild_names = list(EnemyGuild.objects.values_list('name', flat=True))
        try:
            payload = get_online_enemies(configuration.selected_world, guild_names)
            payload['enemies'] = track_enemy_online_sessions(payload['world'], payload['enemies'])
            return Response(payload)
        except (requests.RequestException, ValueError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class CombinedMonitorStatusView(APIView):
    world_name = "Monstera"
    monitor_guilds = {
        "enemy": ["Watch The Throne"],
        "friend": ["Unfallen"],
    }

    def get(self, request):
        try:
            payload = get_monitored_statuses(self.world_name, self.monitor_guilds)
            for monitor_type, monitor in payload['monitors'].items():
                monitor['players'] = track_enemy_online_sessions(
                    payload['world'], monitor['players'], monitor_type=monitor_type,
                )
            return Response(payload)
        except (requests.RequestException, ValueError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})


class SiteAccessStatusView(APIView):
    def get(self, request):
        return Response({'authenticated': bool(getattr(request, 'site_access_authenticated', False))})


class SiteAccessLoginView(APIView):
    def post(self, request):
        configured = settings.SITE_ACCESS_PASSWORD
        supplied = request.data.get('password', '')
        if not configured:
            return Response({'error': 'Site access is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not isinstance(supplied, str) or not compare_digest(supplied, configured):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_403_FORBIDDEN)

        secure = not settings.DEBUG
        response = Response({'authenticated': True})
        response.set_cookie(
            settings.SITE_ACCESS_COOKIE_NAME,
            signing.dumps('granted', salt=COOKIE_SALT),
            max_age=settings.SITE_ACCESS_MAX_AGE,
            httponly=True,
            secure=secure,
            samesite='None' if secure else 'Lax',
            path='/',
        )
        return response


class SiteAccessLogoutView(APIView):
    def post(self, request):
        response = Response({'authenticated': False})
        response.delete_cookie(
            settings.SITE_ACCESS_COOKIE_NAME,
            samesite='None' if not settings.DEBUG else 'Lax',
            path='/',
        )
        return response


class EnemyObservationView(APIView):
    def get(self, request):
        observations = EnemyObservation.objects.all()
        return Response(EnemyObservationSerializer(observations, many=True).data)

    @staticmethod
    def password_is_valid(request):
        supplied = request.data.get('password', '')
        configured = settings.ENEMY_NOTES_EDIT_PASSWORD
        return bool(configured) and isinstance(supplied, str) and compare_digest(supplied, configured)

    def put(self, request):
        if not self.password_is_valid(request):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = EnemyObservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['character_name']
        text = serializer.validated_data['observation']
        if not text:
            EnemyObservation.objects.filter(character_key=name.casefold()).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        observation, created = EnemyObservation.objects.get_or_create(
            character_key=name.casefold(),
            defaults={'character_name': name, 'observation': text},
        )
        if not created:
            observation.observation = text
            observation.save(update_fields=['observation', 'updated_at'])
        return Response(EnemyObservationSerializer(observation).data)

    def delete(self, request):
        if not self.password_is_valid(request):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_403_FORBIDDEN)
        name = str(request.data.get('character_name', '')).strip()
        if not name:
            return Response({'character_name': ['A character name is required.']}, status=status.HTTP_400_BAD_REQUEST)
        EnemyObservation.objects.filter(character_key=name.casefold()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@never_cache
def next_app(request, path=''):
    route = PurePosixPath(path.strip('/'))
    if '..' in route.parts:
        raise Http404('Route not found')

    template_name = 'index.html' if not path else f'{route.as_posix()}/index.html'
    try:
        return render(request, template_name)
    except TemplateDoesNotExist as exc:
        raise Http404('Route not found') from exc


