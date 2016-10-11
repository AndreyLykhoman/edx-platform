from .devstack import *

APPSEMBLER_SECRET_KEY = "secret_key"
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = 'http://10.0.2.2:8080/api'
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

FEATURES["ENABLE_SYSADMIN_DASHBOARD"] = True

# needed to show only users and appsembler courses
FEATURES["ENABLE_COURSE_DISCOVERY"] = False
FEATURES["SHOW_ONLY_APPSEMBLER_AND_OWNED_COURSES"] = True
OAUTH_ENFORCE_SECURE = False

APPSEMBLER_FEATURES = ENV_TOKENS.get('APPSEMBLER_FEATURES', {})
TESTDRIVE_TRIAL_DAYS = APPSEMBLER_FEATURES.get('TESTDRIVE_TRIAL_DAYS', 14)
ENFORCE_TESTDRIVE_EXPIRATION = APPSEMBLER_FEATURES.get('ENFORCE_TESTDRIVE_EXPIRATION', True)
ENFORCE_TESTDRIVE_EXPIRATION_LMS = APPSEMBLER_FEATURES.get('ENFORCE_TESTDRIVE_EXPIRATION_LMS', False)

# disable caching in dev environment
#CACHES['general']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
#CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'


INSTALLED_APPS += ('appsembler_lms',)
