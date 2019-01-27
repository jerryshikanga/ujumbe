import logging
import logging.config

from ujumbe.settings.base import *
from ujumbe.settings import check_if_config_dict_exists

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default='amqp://oakfxmcf:KEc0LZ9y72l000YqU8P-CcZ7gBob4IXC@cat.rmq'
                                                     '.cloudamqp.com/oakfxmcf')

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

AFRICASTALKING_USERNAME = env("AFRICASTALKING_USERNAME")
AFRICASTALKING_API_KEY = env("AFRICASTALKING_API_KEY")

EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")

DEFAULT_FROM_EMAIL = "admin@admin.com"
SERVER_EMAIL = 'server@admin.com'

OPEN_WEATHER_APP_ID = env("OPEN_WEATHER_APPID")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s %(levelname)s %(message)s',
)

LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJECT_DIR, "logs", "debug.log")
        },
    },
    'loggers': {
        # root logger
        '': {
            'level': 'ERROR',
            'handlers': ['file',],
            'format': '%(levelname)s %(asctime)s %(module)s: %(message)s'
        },
    },
})

CUSTOMER_SUPPORT_PHONE = env("CUSTOMER_SUPPORT_EMAIL")
CUSTOMER_SUPPORT_EMAIL = env("CUSTOMER_SUPPORT_TELEPHONE")

NETATMO_USERNAME = env("NETATMO_USERNAME")
NETATMO_PASSWORD = env("NETATMO_PASSWORD")
NETATMO_CLIENT_ID = env("NETATMO_CLIENT_ID")
NETATMO_CLIENT_SECRET = env("NETATMO_CLIENT_SECRET")

GOOGLE_API_KEY = env("GOOGLE_API_KEY")
ACCUWEATHER_API_KEY = env("ACCUWEATHER_API_KEY")

DEFAULT_WEATHER_SOURCE = env("DEFAULT_WEATHER_SOURCE", default="AccuWeather")

TELERIVET_API_KEY = env("TELERIVET_API_KEY", default="")
TELERIVET_PROJECT_ID = env("TELERIVET_PROJECT_ID", default="")
TELERIVET_WEBHOOK_SECRET = env("TELERIVET_WEBHOOK_SECRET", default="")
TELERIVET_SMS_SEND_COST = env("TELERIVET_SMS_SEND_COST", default="")
TELERIVET_SMS_SEND_CURRENCY = env("TELERIVET_SMS_SEND_CURRENCY", default="KES")
