from rest_framework import viewsets, status
from .models import DiscordUser, Character, DiscordUserAndCharacters
from .serializers import DiscordUserSerializer, CharacterSerializer, DiscordUserAndCharactersSerializer
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
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

# Serve React App
index = never_cache(TemplateView.as_view(template_name='index.html'))


