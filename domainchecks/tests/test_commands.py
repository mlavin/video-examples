from datetime import timedelta
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from . import factories


class CheckDomainsCommandTestCase(TestCase):
    """Management command for running the domain checks."""

    def call_command(self, **kwargs):
        """Helper to call the management command and return stdout/stderr."""
        stdout, stderr = StringIO(), StringIO()
        kwargs['stdout'], kwargs['stderr'] = stdout, stderr
        call_command('checkdomains', **kwargs)
        stdout.seek(0)
        stderr.seek(0)
        return stdout, stderr

    def test_no_checks(self):
        """Call command with no checks configured."""
        stdout, stderr = self.call_command()
        self.assertIn('0 domain statuses updated', stdout.getvalue())

    @patch('domainchecks.management.commands.checkdomains.DomainCheck')
    def test_check_stale_domains(self, mock_model):
        """Checks should only be run for active and stale domains."""
        self.call_command()
        cutoff = timedelta(minutes=5)
        mock_model.objects.active.assert_called_with()
        mock_model.objects.active.return_value.stale.assert_called_with(
            cutoff=cutoff)

    @patch('domainchecks.management.commands.checkdomains.DomainCheck')
    def test_specify_cutoff(self, mock_model):
        """Minutes option changes the stale cutoff."""
        self.call_command(minutes=60)
        cutoff = timedelta(minutes=60)
        mock_model.objects.active.return_value.stale.assert_called_with(
            cutoff=cutoff)

    @patch('domainchecks.management.commands.checkdomains.DomainCheck')
    def test_check_run_check(self, mock_model):
        """Checks should use the run_check model method."""
        example = Mock()
        mock_model.objects.active.return_value.stale.return_value = [example, ]
        self.call_command()
        example.run_check.assert_called_with(timeout=10)

    @patch('domainchecks.management.commands.checkdomains.DomainCheck')
    def test_specity_timeout(self, mock_model):
        """Timeout option changes the timeout for run_check."""
        example = Mock()
        mock_model.objects.active.return_value.stale.return_value = [example, ]
        self.call_command(timeout=1)
        example.run_check.assert_called_with(timeout=1)

    def test_functional_defaults(self):
        """Run command defaults with actual domain record."""
        stale = factories.create_domain_check()
        # Still want to mock the remote call
        with patch('domainchecks.models.requests') as mock_requests:
            mock_requests.request.return_value = Mock(
                status_code=200, text='Ok')
            stdout, stderr = self.call_command()
            mock_requests.request.assert_called_once_with(
                stale.method, stale.url, allow_redirects=False, timeout=10)
        self.assertIn('1 domain status updated', stdout.getvalue())
