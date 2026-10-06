import os

import dj_database_url


def database_from_environment(base_dir):
    database_url = os.getenv('DATABASE_URL', '').strip()
    if database_url:
        return dj_database_url.parse(database_url, conn_max_age=600, conn_health_checks=True)

    engine = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
    if engine == 'django.db.backends.sqlite3':
        return {
            'ENGINE': engine,
            'NAME': base_dir / os.getenv('DB_NAME', 'db.sqlite3'),
        }
    return {
        'ENGINE': engine,
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
