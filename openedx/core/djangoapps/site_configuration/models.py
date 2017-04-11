"""
Django models for site configurations.
"""
import collections

import os
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel
from jsonfield.fields import JSONField

from openedx.core.djangoapps.appsembler.sites.utils import get_initial_sass_variables, get_initial_page_elements, \
    compile_sass

from logging import getLogger
logger = getLogger(__name__)  # pylint: disable=invalid-name


class SiteConfiguration(models.Model):
    """
    Model for storing site configuration. These configuration override OpenEdx configurations and settings.
    e.g. You can override site name, logo image, favicon etc. using site configuration.

    Fields:
        site (OneToOneField): one to one field relating each configuration to a single site
        values (JSONField):  json field to store configurations for a site
    """
    site = models.OneToOneField(Site, related_name='configuration')
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    sass_variables = JSONField(blank=True, default=get_initial_sass_variables)
    page_elements = JSONField(blank=True, default=get_initial_page_elements)

    def __unicode__(self):
        return u"<SiteConfiguration: {site} >".format(site=self.site)

    def __repr__(self):
        return self.__unicode__()

    def save(self, **kwargs):
        # When creating a new object, save default microsite values. Not implemented as a default method on the field
        # because it depends on other fields that should be already filled.
        if not self.id and not self.values:
            self.values = self._get_initial_microsite_values()

        # fix for a bug with some pages requiring uppercase platform_name variable
        self.values['PLATFORM_NAME'] = self.values.get('platform_name', '')

        super(SiteConfiguration, self).save(**kwargs)

        # recompile SASS on every save
        self.compile_microsite_sass()
        #self.collect_css_file()
        return self

    def get_value(self, name, default=None):
        """
        Return Configuration value for the key specified as name argument.

        Function logs a message if configuration is not enabled or if there is an error retrieving a key.

        Args:
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key or returns `None` if configuration is not enabled.
        """
        if self.enabled:
            try:
                return self.values.get(name, default)  # pylint: disable=no-member
            except AttributeError as error:
                logger.exception('Invalid JSON data. \n [%s]', error)
        else:
            logger.info("Site Configuration is not enabled for site (%s).", self.site)

        return default

    @classmethod
    def get_value_for_org(cls, org, name, default=None):
        """
        This returns site configuration value which has an org_filter that matches
        what is passed in,

        Args:
            org (str): Course ord filter, this value will be used to filter out the correct site configuration.
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key.
        """
        for configuration in cls.objects.filter(values__contains=org, enabled=True).all():
            org_filter = configuration.get_value('course_org_filter', None)
            if org_filter == org:
                return configuration.get_value(name, default)
        return default

    @classmethod
    def get_all_orgs(cls):
        """
        This returns all of the orgs that are considered in site configurations, This can be used,
        for example, to do filtering.

        Returns:
            A list of all organizations present in site configuration.
        """
        org_filter_set = set()

        for configuration in cls.objects.filter(values__contains='course_org_filter', enabled=True).all():
            org_filter = configuration.get_value('course_org_filter', None)
            if org_filter:
                org_filter_set.add(org_filter)
        return org_filter_set

    @classmethod
    def has_org(cls, org):
        """
        Check if the given organization is present in any of the site configuration.

        Returns:
            True if given organization is present in site configurations otherwise False.
        """
        return org in cls.get_all_orgs()

    def delete(self, using=None):
        self.delete_css_override()
        super(SiteConfiguration, self).delete(using=using)

    def compile_microsite_sass(self):
        css_output = compile_sass('main.scss', custom_branding=self._sass_var_override)
        domain_without_port_number = self.site.domain.split(':')[0]
        if settings.DEBUG:
            from openedx.core.djangoapps.theming.helpers import get_theme_base_dir
            theme_dir = get_theme_base_dir(settings.DEFAULT_SITE_THEME)
            output_path = os.path.join(theme_dir, 'customer_themes')
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_file_path = os.path.join(output_path, '{}.css'.format(domain_without_port_number))
            with open(output_file_path, 'w') as f:
                f.write(css_output.encode('utf-8'))
                os.chmod(output_path, 0777)

        collected_output_path = os.path.join(settings.STATIC_ROOT, 'customer_themes')
        if not os.path.exists(collected_output_path):
            os.makedirs(collected_output_path)
        collected_output_file_path = os.path.join(collected_output_path, '{}.css'.format(domain_without_port_number))
        with open(collected_output_file_path, 'w') as f:
            f.write(css_output.encode('utf-8'))
            os.chmod(collected_output_path, 0777)

    def collect_css_file(self):
        path = self.values.get('css_overrides_file')
        storage = staticfiles_storage
        file_storage = FileSystemStorage(settings.MICROSITE_ROOT_DIR)
        if getattr(file_storage, 'prefix', None):
            prefixed_path = os.path.join(file_storage.prefix, path)
        if settings.DEBUG:
            theme_folder = os.path.join(settings.COMPREHENSIVE_THEME_DIRS[0], 'customer_themes')
        else:
            theme_folder = os.path.join(settings.STATIC_ROOT, '..', 'customer_themes')
        theme_file = os.path.join(theme_folder, '{}.css'.format(domain_without_port_number))
        with open(theme_file, 'w') as f:
            f.write(css_output.encode('utf-8'))
            os.chmod(theme_file, 0777)

    def set_sass_variables(self, entries):
        """
        Accepts a dict with the shape { var_name: value } and sets the SASS variables
        """
        for index, entry in enumerate(self.sass_variables):
            var_name = entry[0]
            if var_name in entries:
                new_value = (var_name, [entries[var_name], entries[var_name]])
                self.sass_variables[index] = new_value

    def delete_css_override(self):
        css_file = self.values.get('css_overrides_file')
        if css_file:
            try:
                os.remove(os.path.join(settings.COMPREHENSIVE_THEME_DIRS[0], css_file))
                os.remove(os.path.join(settings.STATIC_ROOT, '..', 'customer_themes', css_file))
            except OSError:
                logger.warning("Can't delete CSS file {}".format(css_file))

    def _formatted_sass_variables(self):
        return " ".join(["{}: {};".format(var, val[0]) for var, val in self.sass_variables])

    def _sass_var_override(self, path):
        if 'branding-basics' in path:
            return [(path, self._formatted_sass_variables())]
        return None

    def _get_initial_microsite_values(self):
        domain_without_port_number = self.site.domain.split(':')[0]
        if settings.DEBUG:
            css_overrides_file = "customer_themes/{}.css".format(domain_without_port_number),
        else:
            css_overrides_file = "{}.css".format(domain_without_port_number),
        return {
            'platform_name': self.site.name,
            'css_overrides_file': css_overrides_file,
            'ENABLE_COMBINED_LOGIN_REGISTRATION': True,
        }


class SiteConfigurationHistory(TimeStampedModel):
    """
    This is an archive table for SiteConfiguration, so that we can maintain a history of
    changes. Note that the site field is not unique in this model, compared to SiteConfiguration.

    Fields:
        site (ForeignKey): foreign-key to django Site
        values (JSONField): json field to store configurations for a site
    """
    site = models.ForeignKey(Site, related_name='configuration_histories')
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    def __unicode__(self):
        return u"<SiteConfigurationHistory: {site}, Last Modified: {modified} >".format(
            modified=self.modified,
            site=self.site,
        )

    def __repr__(self):
        return self.__unicode__()


@receiver(post_save, sender=SiteConfiguration)
def update_site_configuration_history(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add site configuration changes to site configuration history.

    Args:
        sender: sender of the signal i.e. SiteConfiguration model
        instance: SiteConfiguration instance associated with the current signal
        **kwargs: extra key word arguments
    """
    SiteConfigurationHistory.objects.create(
        site=instance.site,
        values=instance.values,
        enabled=instance.enabled,
    )
