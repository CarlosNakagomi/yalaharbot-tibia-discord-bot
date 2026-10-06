# Railway deployment checklist

This repository is prepared for three Railway services. Do not place real secrets in this file or in source control.

## 1. PostgreSQL service

1. Create a PostgreSQL service in the Railway project.
2. Keep its generated credentials private.
3. Reference its `DATABASE_URL` from the Django service using Railway's variable reference feature.

## 2. Django backend service

- Root directory: repository root (`/`)
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
- Migration command, run as a Railway pre-deploy command: `python manage.py migrate`
- Health-check path: `/api/health/`

Set these variables:

```text
DJANGO_SECRET_KEY=<long random secret>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=<backend Railway hostname without scheme>
DJANGO_CORS_ALLOWED_ORIGINS=https://<frontend Railway hostname>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<frontend Railway hostname>
DJANGO_SECURE_SSL_REDIRECT=true
DATABASE_URL=<reference the PostgreSQL service DATABASE_URL>
SITE_ACCESS_PASSWORD=<private shared site password>
ENEMY_NOTES_EDIT_PASSWORD=<different private observation-edit password>
DISCORD_BOT_TOKEN=<only if this service will also run Discord bot code>
```

Do not set `DB_ENGINE` or `DB_NAME` in production when `DATABASE_URL` is supplied.

## 3. Next.js frontend service

- Root directory: `/frontend`
- Build command: `npm ci && npm run build`
- Start command: `npm run start -- -p $PORT`

Set:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend Railway hostname>
```

This value is public by design and contains only the API origin, never a password.

## 4. Final verification

1. Generate public domains for the backend and frontend services.
2. Insert those domains into the variables above and redeploy both services.
3. Confirm the backend health check returns `{"status":"ok"}`.
4. Confirm an unauthenticated request to `/api/monitors/status/` returns HTTP 401.
5. Open the frontend and log in with `SITE_ACCESS_PASSWORD`.
6. Confirm Enemy and Friend monitors refresh and observations load.
7. Confirm observation editing still requires `ENEMY_NOTES_EDIT_PASSWORD`.
8. Restart the Django service and confirm observations and online timers remain, demonstrating PostgreSQL persistence.
