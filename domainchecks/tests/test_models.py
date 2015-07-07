import datetime

from django.test import TestCase
from django.utils.timezone import now

from .. import models


class DomainChecksTestCase(TestCase):
    """DomainChecks customizations."""

    def create_domain_check(self, **kwargs):
        """Create a sample domain check."""
        values = {
            'protocol': 'http',
            'domain': 'example.com',
            'path': '/',
            'method': 'get',
            'is_active': True,
        }
        values.update(kwargs)
        return models.DomainCheck.objects.create(**values)

    def create_check_result(self, **kwargs):
        """Create a sample check result."""
        values = {
            'checked_on': now(),
            'status_code': 200,
            'response_time': 0.5,
            'response_body': 'Ok'
        }
        values.update(kwargs)
        if 'domain_check' not in values:
            values['domain_check'] = self.create_domain_check()
        return models.CheckResult.objects.create(**values)

    def test_active_manager(self):
        """Active manager should only return active domains."""
        active = self.create_domain_check(is_active=True)
        # Create another inactive
        self.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.active().order_by('pk')
        self.assertQuerysetEqual(
            result, [active.pk], transform=lambda x: x.pk)

    def test_default_manager(self):
        """Default manager should not exclude any domains."""
        active = self.create_domain_check(is_active=True)
        # Create another inactive
        inactive = self.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.all().order_by('pk')
        self.assertQuerysetEqual(
            result, [active.pk, inactive.pk], transform=lambda x: x.pk)

    def test_stale_domains(self):
        """Query for domains which haven't been checked recently."""
        # Domain with a recent check
        recent = self.create_domain_check()
        self.create_check_result(domain_check=recent)
        # Domain with an old check
        stale = self.create_domain_check()
        self.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = self.create_domain_check()
        result = models.DomainCheck.objects.stale().order_by('pk')
        self.assertQuerysetEqual(
            result, [stale.pk, no_results.pk], transform=lambda x: x.pk)

    def test_active_stale_domains(self):
        """Query only active domains which haven't been checked recently."""
        # Domain with a recent check
        recent = self.create_domain_check()
        self.create_check_result(domain_check=recent)
        # Domain with an old check
        stale = self.create_domain_check()
        self.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Inactive domain with an old check
        stale_inactive = self.create_domain_check(is_active=False)
        self.create_check_result(
            domain_check=stale_inactive,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = self.create_domain_check()
        # Inactive domain with no checks
        self.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.active().stale().order_by('pk')
        self.assertQuerysetEqual(
            result, [stale.pk, no_results.pk], transform=lambda x: x.pk)

    def test_variable_stale_cutoff(self):
        """Pass in a non-default cutoff value for the stale check."""
        # Domain with a recent check
        recent = self.create_domain_check()
        self.create_check_result(domain_check=recent)
        # Domain with an old check but within the new cutoff
        stale = self.create_domain_check()
        self.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = self.create_domain_check()
        result = models.DomainCheck.objects.stale(
            cutoff=datetime.timedelta(days=2)).order_by('pk')
        self.assertQuerysetEqual(
            result, [no_results.pk, ], transform=lambda x: x.pk)

