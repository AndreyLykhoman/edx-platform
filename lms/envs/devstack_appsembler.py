# devstack_appsembler.py

from .devstack import *
from .appsembler import *
import dj_database_url

OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

INSTALLED_APPS += (
    'django_extensions',
    'openedx.core.djangoapps.appsembler.sites',
)

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'cache-control'
)
DEBUG_TOOLBAR_PATCH_SETTINGS = False

#SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'organizations.backends.DefaultSiteBackend',
    'organizations.backends.SiteMemberBackend',
    'organizations.backends.OrganizationMemberBackend',
)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

EDX_API_KEY = "test"

INSTALLED_APPS += (
    'hijack',
    'compat',
    'hijack_admin',
    'tiers',
)
MIDDLEWARE_CLASSES += (
    'organizations.middleware.OrganizationMiddleware',
#    'tiers.middleware.TierMiddleware',
)

COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'
SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
TIERS_EXPIRED_REDIRECT_URL = None

TIERS_DATABASE_URL = AUTH_TOKENS.get('TIERS_DATABASE_URL')
DATABASES['tiers'] = dj_database_url.parse(TIERS_DATABASE_URL)

DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']

COURSE_TO_CLONE = "course-v1:Appsembler+CC101+2017"

CELERY_ALWAYS_EAGER = True

ALTERNATE_QUEUE_ENVS = ['cms']
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in ALTERNATE_QUEUE_ENVS
]
CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in CELERY_QUEUES.keys()
    }
)

CLONE_COURSE_FOR_NEW_SIGNUPS = False
HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

USE_S3_FOR_CUSTOMER_THEMES = False
CUSTOMER_THEMES_LOCAL_DIR = os.path.join(COMPREHENSIVE_THEME_DIRS[0], 'customer_themes')
