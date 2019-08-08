import logging
import logging.config

from ujumbe.settings.base import *
from ujumbe.settings import check_if_config_dict_exists

# celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

AFRICASTALKING_USERNAME = env("AFRICASTALKING_USERNAME", default="")
AFRICASTALKING_API_KEY = env("AFRICASTALKING_API_KEY", default="")

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT", default="")
EMAIL_HOST_USER = env("EMAIL_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", default=True)

DEFAULT_FROM_EMAIL = "admin@admin.com"
SERVER_EMAIL = 'server@admin.com'

OPEN_WEATHER_APP_ID = env("OPEN_WEATHER_APPID", default="")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s %(levelname)s %(message)s',
)

LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJECT_DIR, "logs", "debug.log"),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        # root logger
        '': {
            'level': 'WARNING',
            'handlers': ['file', ],
            'formatter': 'verbose'
        },
    },
})

CUSTOMER_SUPPORT_PHONE = env("CUSTOMER_SUPPORT_EMAIL", default="")
CUSTOMER_SUPPORT_EMAIL = env("CUSTOMER_SUPPORT_TELEPHONE", default="")

NETATMO_USERNAME = env("NETATMO_USERNAME", default="")
NETATMO_PASSWORD = env("NETATMO_PASSWORD", default="")
NETATMO_CLIENT_ID = env("NETATMO_CLIENT_ID", default="")
NETATMO_CLIENT_SECRET = env("NETATMO_CLIENT_SECRET", default="")

GOOGLE_API_KEY = env("GOOGLE_API_KEY", default="")
ACCUWEATHER_API_KEY = env("ACCUWEATHER_API_KEY", default="")

DEFAULT_WEATHER_SOURCE = env("DEFAULT_WEATHER_SOURCE", default="AccuWeather")

TELERIVET_API_KEY = env("TELERIVET_API_KEY", default=None)
TELERIVET_PROJECT_ID = env("TELERIVET_PROJECT_ID", default=None)
TELERIVET_WEBHOOK_SECRET = env("TELERIVET_WEBHOOK_SECRET", default="")
TELERIVET_SMS_SEND_COST = env("TELERIVET_SMS_SEND_COST", default="")
TELERIVET_SMS_SEND_CURRENCY = env("TELERIVET_SMS_SEND_CURRENCY", default="KES")

YANDEX_TRANSLATE_API_KEY = env("YANDEX_TRANSLATE_API_KEY", default="")
YANDEX_TRANSLATE_API_URL = "https://translate.yandex.net/api/v1.5/tr/translate"
