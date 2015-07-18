from unittest.mock import Mock

from django.contrib.admin import site
from django.test import RequestFactory, TestCase

from .. import admin, models
from . import factories


class StatusListFilterTestCase(TestCase):
    """Custom list filter for domain check status."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = admin.DomainCheckAdmin(models.DomainCheck, site)

    def get_list_filter(self, request):
        return admin.StatusListFilter(
            request, dict(request.GET.items()), models.DomainCheck, self.admin)

    def test_lookups(self):
        """Get the set of available lookup options."""
        request = self.factory.get('/admin/')
        list_filter = self.get_list_filter(request)
        result = list_filter.lookups(request, self.admin)
        expected = (
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('unknown', 'Unknown'),
        )
        self.assertEqual(result, expected)

    def test_queryset(self):
        """Filter the given queryset to the selected status."""
        request = self.factory.get('/admin/', {'status': 'good'})
        list_filter = self.get_list_filter(request)
        qs = Mock()
        result = list_filter.queryset(request, qs)
        self.assertIsNotNone(result)
        qs.filter.assert_called_with(status='good')

    def test_queryset_invalid_value(self):
        """Invalid string values will still be passed to the queryset filter."""
        request = self.factory.get('/admin/', {'status': 'xxxx'})
        list_filter = self.get_list_filter(request)
        qs = Mock()
        result = list_filter.queryset(request, qs)
        self.assertIsNotNone(result)
        qs.filter.assert_called_with(status='xxxx')

    def test_queryset_no_value(self):
        """Queryset will not be filtered if no value was given."""
        request = self.factory.get('/admin/')
        list_filter = self.get_list_filter(request)
        qs = Mock()
        result = list_filter.queryset(request, qs)
        self.assertIsNone(result)
        self.assertFalse(qs.filter.called)

    def test_functional(self):
        """Apply the filter to an actual queryset."""
        request = self.factory.get('/admin/', {'status': 'good'})
        list_filter = self.get_list_filter(request)
        good = factories.create_check_result(status_code=200).domain_check
        unknown = factories.create_domain_check()
        qs = self.admin.get_queryset(request)
        self.assertQuerysetEqual(
            qs.order_by('pk'), [good.pk, unknown.pk, ], transform=lambda x: x.pk)
        result = list_filter.queryset(request, qs)
        self.assertQuerysetEqual(
            result.order_by('pk'), [good.pk, ], transform=lambda x: x.pk)
