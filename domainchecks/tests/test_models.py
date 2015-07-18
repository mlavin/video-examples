import datetime

from unittest.mock import Mock, patch

from requests import ConnectionError, HTTPError, Timeout

from django.test import TestCase
from django.utils.timezone import now

from .. import models
from . import factories


class DomainChecksTestCase(TestCase):
    """DomainChecks customizations."""

    def test_active_manager(self):
        """Active manager should only return active domains."""
        active = factories.create_domain_check(is_active=True)
        # Create another inactive
        factories.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.active().order_by('pk')
        self.assertQuerysetEqual(
            result, [active.pk], transform=lambda x: x.pk)

    def test_default_manager(self):
        """Default manager should not exclude any domains."""
        active = factories.create_domain_check(is_active=True)
        # Create another inactive
        inactive = factories.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.all().order_by('pk')
        self.assertQuerysetEqual(
            result, [active.pk, inactive.pk], transform=lambda x: x.pk)

    def test_stale_domains(self):
        """Query for domains which haven't been checked recently."""
        # Domain with a recent check
        recent = factories.create_domain_check()
        factories.create_check_result(domain_check=recent)
        # Domain with an old check
        stale = factories.create_domain_check()
        factories.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = factories.create_domain_check()
        result = models.DomainCheck.objects.stale().order_by('pk')
        self.assertQuerysetEqual(
            result, [stale.pk, no_results.pk], transform=lambda x: x.pk)

    def test_active_stale_domains(self):
        """Query only active domains which haven't been checked recently."""
        # Domain with a recent check
        recent = factories.create_domain_check()
        factories.create_check_result(domain_check=recent)
        # Domain with an old check
        stale = factories.create_domain_check()
        factories.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Inactive domain with an old check
        stale_inactive = factories.create_domain_check(is_active=False)
        factories.create_check_result(
            domain_check=stale_inactive,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = factories.create_domain_check()
        # Inactive domain with no checks
        factories.create_domain_check(is_active=False)
        result = models.DomainCheck.objects.active().stale().order_by('pk')
        self.assertQuerysetEqual(
            result, [stale.pk, no_results.pk], transform=lambda x: x.pk)

    def test_variable_stale_cutoff(self):
        """Pass in a non-default cutoff value for the stale check."""
        # Domain with a recent check
        recent = factories.create_domain_check()
        factories.create_check_result(domain_check=recent)
        # Domain with an old check but within the new cutoff
        stale = factories.create_domain_check()
        factories.create_check_result(
            domain_check=stale,
            checked_on=now() - datetime.timedelta(days=1))
        # Domain with no checks
        no_results = factories.create_domain_check()
        result = models.DomainCheck.objects.stale(
            cutoff=datetime.timedelta(days=2)).order_by('pk')
        self.assertQuerysetEqual(
            result, [no_results.pk, ], transform=lambda x: x.pk)

    def test_single_check_status(self):
        """Annotated status for a single check."""
        check = factories.create_domain_check()
        # Now
        factories.create_check_result(domain_check=check)
        # 15 mins ago (failure)
        factories.create_check_result(
            domain_check=check, status_code=500,
            checked_on=now() - datetime.timedelta(minutes=15))
        # 30 mins ago (failure)
        factories.create_check_result(
            domain_check=check, status_code=403,
            checked_on=now() - datetime.timedelta(minutes=30))
        # 45 mins ago
        factories.create_check_result(
            domain_check=check,
            checked_on=now() - datetime.timedelta(minutes=15))
        result = models.DomainCheck.objects.status().get(pk=check.pk)
        self.assertEqual(result.successes, 2)
        self.assertEqual(result.pings, 4)
        self.assertEqual(result.success_rate, 50.0)
        self.assertEqual(result.status, 'poor')

    def test_multiple_check_status(self):
        """Annotate a queryset of multiple domain checks."""
        good = factories.create_domain_check()
        fair = factories.create_domain_check()
        poor = factories.create_domain_check()
        # Domain with no checks will have an unknown status
        factories.create_domain_check()
        # Now
        factories.create_check_result(domain_check=good)
        factories.create_check_result(domain_check=fair)
        factories.create_check_result(domain_check=poor)
        # 15 mins ago
        factories.create_check_result(
            domain_check=fair, status_code=500,
            checked_on=now() - datetime.timedelta(minutes=15))
        factories.create_check_result(
            domain_check=poor, status_code=500,
            checked_on=now() - datetime.timedelta(minutes=15))
        # 30 mins ago
        factories.create_check_result(
            domain_check=fair,
            checked_on=now() - datetime.timedelta(minutes=30))
        factories.create_check_result(
            domain_check=poor, status_code=403,
            checked_on=now() - datetime.timedelta(minutes=30))
        # 45 mins ago
        factories.create_check_result(
            domain_check=fair,
            checked_on=now() - datetime.timedelta(minutes=15))
        factories.create_check_result(
            domain_check=poor,
            checked_on=now() - datetime.timedelta(minutes=15))
        result = models.DomainCheck.objects.status().order_by('pk')
        self.assertQuerysetEqual(
            result, ['good', 'fair', 'poor', 'unknown', ],
            transform=lambda x: x.status)

    @patch('requests.request')
    def test_run_check_success(self, mock_fetch):
        """Fetch a page succesfully and save the result."""
        mock_fetch.return_value = Mock(status_code=200, text='Ok')
        domain = factories.create_domain_check()
        domain.run_check()
        checks = domain.checkresult_set.all()
        self.assertEqual(checks.count(), 1)
        check = checks[0]
        self.assertEqual(check.checked_on.date(), now().date())
        self.assertGreater(check.response_time, 0)
        self.assertEqual(check.status_code, 200)
        self.assertEqual(check.response_body, 'Ok')

    @patch('requests.request')
    def test_run_check_failure(self, mock_fetch):
        """Fetch a page with an error status and save the result."""
        result = Mock(status_code=404, text='Not Found')
        result.raise_for_status.side_effect = HTTPError
        mock_fetch.return_value = result
        domain = factories.create_domain_check()
        domain.run_check()
        checks = domain.checkresult_set.all()
        self.assertEqual(checks.count(), 1)
        check = checks[0]
        self.assertEqual(check.checked_on.date(), now().date())
        self.assertGreater(check.response_time, 0)
        self.assertEqual(check.status_code, 404)
        self.assertEqual(check.response_body, 'Not Found')

    @patch('requests.request')
    def test_run_check_timeout(self, mock_fetch):
        """Fetch a page which times out and save the result."""
        mock_fetch.side_effect = Timeout
        domain = factories.create_domain_check()
        domain.run_check()
        checks = domain.checkresult_set.all()
        self.assertEqual(checks.count(), 1)
        check = checks[0]
        self.assertEqual(check.checked_on.date(), now().date())
        self.assertGreater(check.response_time, 0)
        self.assertIsNone(check.status_code)
        self.assertEqual(check.response_body, '')

    @patch('requests.request')
    def test_run_check_connection_error(self, mock_fetch):
        """Fetch a page which can't connect and save the result."""
        mock_fetch.side_effect = ConnectionError
        domain = factories.create_domain_check()
        domain.run_check()
        checks = domain.checkresult_set.all()
        self.assertEqual(checks.count(), 1)
        check = checks[0]
        self.assertEqual(check.checked_on.date(), now().date())
        self.assertGreater(check.response_time, 0)
        self.assertIsNone(check.status_code)
        self.assertEqual(check.response_body, '')
