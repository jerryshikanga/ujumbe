from ujumbe.settings.base import *
from ujumbe.settings import check_if_config_dict_exists

check_if_config_dict_exists(value_key="AFRICASTALKING", config_dict=config)
AFRICASTALKING_USERNAME = config['AFRICASTALKING']['username']
AFRICASTALKING_API_KEY = config['AFRICASTALKING']['api_key']

check_if_config_dict_exists(value_key="EMAIL", config_dict=config)
EMAIL_HOST = config["EMAIL"]["host"]
EMAIL_PORT = config["EMAIL"]["port"]
EMAIL_HOST_USER = config["EMAIL"]["user"]
EMAIL_HOST_PASSWORD = config["EMAIL"]["password"]
EMAIL_USE_TLS = get_boolean_value_from_config(config["EMAIL"]["tls"])
EMAIL_USE_SSL = get_boolean_value_from_config(config["EMAIL"]["ssl"])
EMAIL_TIMEOUT = None

DEFAULT_FROM_EMAIL = "admin@admin.com"
SERVER_EMAIL = 'server@admin.com'

check_if_config_dict_exists(value_key="OPENWEATHER", config_dict=config)
OPEN_WEATHER_APP_ID = config["OPEN_WEATHER"]["app_id"]

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


check_if_config_dict_exists(value_key="SUPPORT", config_dict=config)
CUSTOMER_SUPPORT_PHONE = config["SUPPORT"]["phone"]
CUSTOMER_SUPPORT_EMAIL = config["SUPPORT"]["email"]


check_if_config_dict_exists(value_key="NETATMO", config_dict=config)
NETATMO_USERNAME = config["NETATMO"]["username"]
NETATMO_PASSWORD = config["NETATMO"]["password"]
NETATMO_CLIENT_ID = config["NETATMO"]["client_id"]
NETATMO_CLIENT_SECRET = config["NETATMO"]["client_secret"]
