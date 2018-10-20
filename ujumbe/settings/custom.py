from ujumbe.settings.base import *

if 'AFRICASTALKING' not in config:
    logging.error("AFRICASTALKING not in {} file".format(SETTINGS_INI_PATH))
    raise KeyError("AFRICASTALKING not in {} file".format(SETTINGS_INI_PATH))

AFRICASTALKING_USERNAME = config['AFRICASTALKING']['username']
AFRICASTALKING_API_KEY = config['AFRICASTALKING']['api_key']


if 'EMAIL' not in config:
    logging.error("No email setting found")
    raise KeyError("No email setting found")

EMAIL_HOST = config["EMAIL"]["host"]
EMAIL_PORT = config["EMAIL"]["port"]
EMAIL_HOST_USER = config["EMAIL"]["user"]
EMAIL_HOST_PASSWORD = config["EMAIL"]["password"]
EMAIL_USE_TLS = get_boolean_value_from_config(config["EMAIL"]["tls"])
EMAIL_USE_SSL = get_boolean_value_from_config(config["EMAIL"]["ssl"])
EMAIL_TIMEOUT = None

DEFAULT_FROM_EMAIL = "admin@admin.com"
SERVER_EMAIL = 'server@admin.com'

if 'OPEN_WEATHER' not in config :
    logging.error("No open weather api setting found")
    raise KeyError("No open weather api setting found")

OPEN_WEATHER_APP_ID = config["OPEN_WEATHER"]["app_id"]

DEFAULT_USSD_SCREEN_JOURNEY = os.path.join(BASE_DIR, "apps", "ussd_app", "yaml", "initial.yaml")

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


if "SUPPORT" not in config:
    message = "Support config options missing in config file"
    logging.error(message)
    raise ValueError(message)

CUSTOMER_SUPPORT_PHONE = config["SUPPORT"]["phone"]
CUSTOMER_SUPPORT_EMAIL = config["SUPPORT"]["email"]


if "NETATMO" not in config:
    message = "Netatmo config options missing in config file"
    logging.error(message)
    raise ValueError(message)


NETATMO_USERNAME = config["NETATMO"]["username"]
NETATMO_PASSWORD = config["NETATMO"]["password"]
NETATMO_CLIENT_ID = config["NETATMO"]["client_id"]
NETATMO_CLIENT_SECRET = config["NETATMO"]["client_secret"]