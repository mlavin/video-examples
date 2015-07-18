from unittest.mock import Mock, patch

from django.contrib.admin import site
from django.test import RequestFactory, TestCase
from django.utils.timezone import now

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


class DomainCheckAdminTestCase(TestCase):
    """Customizations to the domain checks admin."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = admin.DomainCheckAdmin(models.DomainCheck, site)

    def test_get_queryset(self):
        """Default queryset should include the status field annotations."""
        example = factories.create_domain_check()
        self.assertFalse(hasattr(example, 'status'))
        self.assertFalse(hasattr(example, 'last_check'))
        request = self.factory.get('/admin/')
        result = self.admin.get_queryset(request)
        self.assertEqual(result.count(), 1)
        domain = result[0]
        self.assertTrue(hasattr(domain, 'status'))
        self.assertTrue(hasattr(domain, 'last_check'))

    def test_format_status(self):
        """Status field should be title cased."""
        example = Mock()
        example.status = 'good'
        result = self.admin.status(example)
        self.assertEqual(result, 'Good')

    def test_format_last_check(self):
        """Last check should be formatted as timesince the current time."""
        example = Mock()
        example.last_check = now()
        result = self.admin.last_checked(example)
        self.assertEqual(result, '0\xa0minutes ago')

    def test_format_no_last_check(self):
        """If there is no last check it should display 'Never'."""
        example = Mock()
        example.last_check = None
        result = self.admin.last_checked(example)
        self.assertEqual(result, 'Never')

    def test_run_check(self):
        """Run check action should call the run_check model method."""
        example = Mock()
        qs = [example, ]
        request = self.factory.get('/admin/')
        self.admin.run_check(request, qs)
        example.run_check.assert_called_with()

    def test_mark_inactive(self):
        """Selected items should be changed in is_active=False."""
        selected = factories.create_domain_check()
        not_selected = factories.create_domain_check()
        request = self.factory.get('/admin/')
        qs = self.admin.get_queryset(request).filter(pk=selected.pk)
        # Mock the contrib.messages middleware
        with patch.object(self.admin, 'message_user') as mock_message:
            self.admin.mark_inactive(request, qs)
            mock_message.assert_called_with(
                request, '1 domain was made inactive.')
        selected.refresh_from_db()
        not_selected.refresh_from_db()
        self.assertFalse(selected.is_active)
        self.assertTrue(not_selected.is_active)
