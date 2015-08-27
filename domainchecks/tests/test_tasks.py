import datetime
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils.timezone import now

from .. import tasks
from . import factories


@patch('domainchecks.models.requests')
class CheckDomainTestCase(TestCase):
    """Task to update the status of all checks for a given domain."""

    def setUp(self):
        self.check = factories.create_domain_check()
        self.domain = self.check.domain

    def test_defaults(self, mock_requests):
        """Call task with default arguments to run check."""
        mock_requests.request.return_value = Mock(
            status_code=200, text='Ok')
        tasks.check_domain(name=self.domain.name)
        mock_requests.request.assert_called_once_with(
            self.check.method, self.check.url,
            allow_redirects=False, timeout=10)

    def test_configure_timeout(self, mock_requests):
        """Timeout for the server request is configurable."""
        mock_requests.request.return_value = Mock(
            status_code=200, text='Ok')
        tasks.check_domain(name=self.domain.name, timeout=60)
        mock_requests.request.assert_called_once_with(
            self.check.method, self.check.url,
            allow_redirects=False, timeout=60)

    def test_invalid_domain(self, mock_requests):
        """Handle the case where the domain doesn't exist."""
        tasks.check_domain(name='does.not.exist')
        self.assertFalse(mock_requests.called)

    def test_no_checks(self, mock_requests):
        """Handle the case where there are no checks for the domain."""
        self.check.delete()
        tasks.check_domain(name=self.domain.name)
        self.assertFalse(mock_requests.called)

    def test_no_active_checks(self, mock_requests):
        """Handle the case where no checks are active."""
        self.check.is_active = False
        self.check.save(update_fields=('is_active', ))
        tasks.check_domain(name=self.domain.name)
        self.assertFalse(mock_requests.called)

    def test_no_stale_checks(self, mock_requests):
        """Handle the case where all checks have been recently checked."""
        factories.create_check_result(domain_check=self.check)
        tasks.check_domain(name=self.domain.name)
        self.assertFalse(mock_requests.called)

    def test_configure_cutoff(self, mock_requests):
        """Cut off is configurable for which checks are refreshed."""
        other = factories.create_domain_check(domain=self.domain, path='/other/')
        factories.create_check_result(
            domain_check=other, checked_on=now() - datetime.timedelta(minutes=5))
        recent = factories.create_domain_check(domain=self.domain, path='/recent/')
        factories.create_check_result(domain_check=recent)
        mock_requests.request.return_value = Mock(
            status_code=200, text='Ok')
        tasks.check_domain(name=self.domain.name, minutes=4)
        self.assertEqual(mock_requests.request.call_count, 2)
        mock_requests.request.assert_any_call(
            self.check.method, self.check.url,
            allow_redirects=False, timeout=10)
        mock_requests.request.assert_any_call(
            other.method, other.url,
            allow_redirects=False, timeout=10)


@patch('domainchecks.tasks.group')
@patch('domainchecks.tasks.check_domain.s')
class QueueDomainsTestCase(TestCase):
    """Fan out checks for domains with active checks."""

    def setUp(self):
        self.check = factories.create_domain_check()
        self.domain = self.check.domain

    def test_queue_domains(self, mock_check, mock_group):
        """Queue active domains to be checked."""
        factories.create_domain_check(is_active=False)
        tasks.queue_domains()
        mock_check.assert_called_once_with(
            self.domain.name, minutes=10, timeout=10)
        mock_group.assert_called_once_with(mock_check.return_value)
        mock_group.return_value.delay.assert_called_one_with()

    def test_pass_arguments(self, mock_check, mock_group):
        """Minutes and timeout arguments should be passed to the subtask."""
        tasks.queue_domains(minutes=5, timeout=1)
        mock_check.assert_called_once_with(
            self.domain.name, minutes=5, timeout=1)

    def test_multiple_checks(self, mock_check, mock_group):
        """Domains with multiple checks should only be queued once."""
        factories.create_domain_check(domain=self.domain, path='/other/')
        tasks.queue_domains()
        mock_check.assert_called_once_with(
            self.domain.name, minutes=10, timeout=10)
