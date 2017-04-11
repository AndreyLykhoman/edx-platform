# devstack_appsembler.py

from .devstack import *
from .appsembler import *
import dj_database_url

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
)

OAUTH_ENFORCE_SECURE = False

AMC_APP_URL = ENV_TOKENS.get('AMC_APP_URL')

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

INSTALLED_APPS += ('tiers',)
MIDDLEWARE_CLASSES += ('organizations.middleware.OrganizationMiddleware', 'tiers.middleware.TierMiddleware',)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
TIERS_EXPIRED_REDIRECT_URL = AMC_APP_URL + "/expired"

TIERS_DATABASE_URL = AUTH_TOKENS.get('TIERS_DATABASE_URL')
DATABASES['tiers'] = dj_database_url.parse(TIERS_DATABASE_URL)

DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']
