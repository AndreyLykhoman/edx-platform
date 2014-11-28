import os
from .aws import *

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.mandrillapp.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "nate@appsembler.com"
EMAIL_HOST_PASSWORD = os.environ.get("MANDRILL_API_KEY", "")

LMS_BASE = os.environ.get("EDX_LMS_BASE", "")
CMS_BASE = os.environ.get("EDX_CMS_BASE", "")
FEATURES.update(PREVIEW_LMS_BASE=os.environ.get("EDX_PREVIEW_LMS_BASE", ""))

SITE_NAME = LMS_BASE
PLATFORM_NAME = 'Appsembler Open edX Testdrive'
DEFAULT_FROM_EMAIL = 'registration@appsembler.com'

# Allows putting Intercom env variables passed from Docker into templates
TEMPLATE_CONTEXT_PROCESSORS += ('appsembler.context_processors.intercom',)
