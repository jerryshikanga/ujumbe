from ujumbe.settings.base import *
from ujumbe.settings import check_if_config_dict_exists

AFRICASTALKING_USERNAME = env("AFRICASTALKING_USERNAME")
AFRICASTALKING_API_KEY = env("AFRICASTALKING_API_KEY")
AT_USSD_IS_SHARED = env("AT_USSD_IS_SHARED", default=False)
AT_USSD_SHARED_NUMBER = env("AT_USSD_SHARED_NUMBER", default=0)
AT_SMS_IS_SHARED = env("AT_SMS_IS_SHARED", default=False)
AT_SMS_SHARED_KEYWORD = env("AT_SMS_SHARED_KEYWORD", default="")

EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")

DEFAULT_FROM_EMAIL = "admin@admin.com"
SERVER_EMAIL = 'server@admin.com'

OPEN_WEATHER_APP_ID = env("OPEN_WEATHER_APPID")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "..", "debug.log"),
        },
    },
    'loggers': {
        'django': {

        },
    },
}


CUSTOMER_SUPPORT_PHONE = env("CUSTOMER_SUPPORT_EMAIL")
CUSTOMER_SUPPORT_EMAIL = env("CUSTOMER_SUPPORT_TELEPHONE")

NETATMO_USERNAME = env("NETATMO_USERNAME")
NETATMO_PASSWORD = env("NETATMO_PASSWORD")
NETATMO_CLIENT_ID = env("NETATMO_CLIENT_ID")
NETATMO_CLIENT_SECRET = env("NETATMO_CLIENT_SECRET")

GOOGLE_API_KEY = env("GOOGLE_API_KEY")
