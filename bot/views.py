from rest_framework import viewsets, status
from .models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
)
from .serializers import (
    DiscordUserSerializer,
    CharacterSerializer,
    CharacterDeathSerializer,
    DiscordServerSettingsSerializer,
    DiscordUserAndCharactersSerializer,
    WatchedGuildSerializer,
    WatchedWorldSerializer,
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
import requests


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


