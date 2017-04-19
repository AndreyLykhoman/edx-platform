from .aws import *
import dj_database_url

APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
)

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',)

MANDRILL_API_KEY = AUTH_TOKENS.get("MANDRILL_API_KEY")

AMC_APP_URL = ENV_TOKENS.get('AMC_APP_URL')

if MANDRILL_API_KEY:
    EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', 'anymail.backends.mandrill.MandrillBackend')
    ANYMAIL = {
        "MANDRILL_API_KEY": MANDRILL_API_KEY,
    }
    INSTALLED_APPS += ("anymail",)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True

SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
ELASTIC_FIELD_MAPPINGS = {
    "start_date": {
        "type": "date"
    }
}

# SENTRY
SENTRY_DSN = AUTH_TOKENS.get('SENTRY_DSN', False)

if SENTRY_DSN:
    # Set your DSN value
    RAVEN_CONFIG = {
        'environment': FEATURES['ENVIRONMENT'],  # This should be moved somewhere more sensible
        'tags': {
            'app': 'edxapp',
            'service': 'cms'
        },
        'dsn': SENTRY_DSN,
    }

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

INSTALLED_APPS += ('tiers',)
MIDDLEWARE_CLASSES += ('organizations.middleware.OrganizationMiddleware', 'tiers.middleware.TierMiddleware',)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
TIERS_EXPIRED_REDIRECT_URL = AMC_APP_URL + "/expired"

TIERS_DATABASE_URL = AUTH_TOKENS.get('TIERS_DATABASE_URL')
DATABASES['tiers'] = dj_database_url.parse(TIERS_DATABASE_URL)

DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']

XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5
