from django.conf import settings
from django.core.management.base import BaseCommand

from salesforce_registration.models import SalesforceDomainEntry

from simple_salesforce import Salesforce

#turn this into cron job to run nightly and the results cached
#TODO: handle courses being deleted from salesforce
class Command(BaseCommand):
    help = """Sync columns from Salesforce Partner/Customer columns with MySQL."""

    def handle(self, *args, **options):
        update_count = 0

        username = settings.APPSEMBLER_FEATURES['SALESFORCE_USERNAME']
        password = settings.APPSEMBLER_FEATURES['SALESFORCE_PASSWORD']
        token = settings.APPSEMBLER_FEATURES['SALESFORCE_TOKEN']

        sf = Salesforce(password=password, username=username, security_token=token)
        

        categories = ['Partner', 'Customer']

        #add employee if it doesn't exist
        employee = SalesforceDomainEntry.objects.filter(domain='metalogix.com')
        if not employee:
            employee = SalesforceDomainEntry(domain='metalogix.com', category='Employee')
            employee.save()
            update_count += 1

        #add entry for dell employees
        dell = SalesforceDomainEntry.objects.filter(domain='software.dell.com')
        if not dell:
            dell = SalesforceDomainEntry(domain='software.dell.com', category='Dell')
            dell.save()
            update_count += 1

        #query salesforce for partners
        query_result = sf.query_all("SELECT Email_Domain__c FROM Account WHERE Type='{}'".format('Partner')) 
        records = query_result['records']
        for record in records:
            email_domain = record['Email_Domain__c']
            if not email_domain:
                continue

            email_domain = email_domain.lower()
            entry = SalesforceDomainEntry.objects.filter(domain=email_domain)
            if not entry:
                entry = SalesforceDomainEntry(domain=email_domain, category='Partner')
                entry.save()

                update_count += 1

        #query salesforce for customers
        query_result = sf.query_all("SELECT Email_Domain__c FROM Account WHERE customer__c={}".format(True))
        records = query_result['records']
        for record in records:
            email_domain = record['Email_Domain__c']
            if not email_domain:
                continue

            email_domain = email_domain.lower()
            entry = SalesforceDomainEntry.objects.filter(domain=email_domain)
            if not entry:
                entry = SalesforceDomainEntry(domain=email_domain, category='Customer')
                entry.save()

                update_count += 1

        print 'Updated %d Salesforce domain entries' % update_count
