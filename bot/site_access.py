from django.conf import settings
from django.core import signing
from django.http import JsonResponse


COOKIE_SALT = 'tibia-monitor-site-access'
PROTECTED_PREFIXES = (
    '/api/monitors/',
    '/api/enemy-list/',
    '/api/enemy-guilds/',
)


def has_site_access(request):
    token = request.COOKIES.get(settings.SITE_ACCESS_COOKIE_NAME)
    if not token:
        return False
    try:
        return signing.loads(token, salt=COOKIE_SALT, max_age=settings.SITE_ACCESS_MAX_AGE) == 'granted'
    except signing.BadSignature:
        return False


class SiteAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.site_access_authenticated = has_site_access(request)
        if request.path.startswith(PROTECTED_PREFIXES) and not request.site_access_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        return self.get_response(request)
