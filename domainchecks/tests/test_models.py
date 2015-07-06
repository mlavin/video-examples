from django.test import TestCase

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

    def test_active_manager(self):
        """Active manager should only return active domains."""
        active = self.create_domain_check(is_active=True)
        # Create another inactive
        self.create_domain_check(is_active=False)
        result = models.DomainCheck.active.all().order_by('pk')
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
