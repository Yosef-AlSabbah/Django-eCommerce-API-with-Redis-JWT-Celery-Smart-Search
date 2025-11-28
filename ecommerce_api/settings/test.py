from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'

# Disable throttling for tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
