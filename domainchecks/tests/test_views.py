from unittest.mock import Mock

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import RequestFactory, TestCase

from .. import views
from . import factories


class StatusListViewTestCase(TestCase):
    """Listing all active domains."""

    def setUp(self):
        self.url = reverse('status-list')
        self.factory = RequestFactory()
        self.view = views.StatusList.as_view()

    def test_render_domains(self):
        """Page should render all active domains."""
        factories.create_domain_check(domain='example.com')
        factories.create_domain_check(domain='djangoproject.com')
        factories.create_domain_check(
            domain='evil.com', is_active=False)
        with self.assertTemplateUsed('domainchecks/status-list.html'):
            response = self.client.get(self.url)
            self.assertContains(response, 'example.com')
            self.assertContains(response, 'djangoproject.com')
            self.assertNotContains(response, 'evil.com')

    def test_no_domains(self):
        """Page will still render if there are no domains."""
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)


class StatusDetailViewTestCase(TestCase):
    """All checks for a single active domain."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.StatusDetail.as_view()

    def test_no_checks_found(self):
        """Page should 404 if there are no checks for a given domain."""
        url = reverse('status-detail', kwargs={'domain': 'unknown.com'})
        request = self.factory.get(url)
        with self.assertRaises(Http404):
            self.view(request, domain='unknown.com')

    def test_no_active_checks(self):
        """Page should 404 if there are no active checks for the domain."""
        check = factories.create_domain_check(is_active=False)
        url = reverse('status-detail', kwargs={'domain': check.domain})
        request = self.factory.get(url)
        with self.assertRaises(Http404):
            self.view(request, domain=check.domain)

    def test_query_matched_domain(self):
        """Checks should be filtered to the requested domain."""
        check = factories.create_domain_check(domain='example.com')
        factories.create_domain_check(domain='other.com')
        url = reverse('status-detail', kwargs={'domain': check.domain})
        view = views.StatusDetail()
        view.request = self.factory.get(url)
        view.args = []
        view.kwargs = {'domain': check.domain}
        qs = view.get_queryset()
        self.assertQuerysetEqual(
            qs, [check.pk, ], transform=lambda x: x.pk)

    def test_render_checks(self):
        """Render the active checks for a given domain."""
        check = factories.create_domain_check(domain='example.com')
        factories.create_domain_check(
            domain=check.domain, path='/extra/')
        url = reverse('status-detail', kwargs={'domain': check.domain})
        with self.assertTemplateUsed('domainchecks/status-detail.html'):
            response = self.client.get(url)
            self.assertContains(response, 'HTTP GET /')
            self.assertContains(response, 'HTTP GET /extra/')


class CheckTimelineViewTestCase(TestCase):
    """JSON list of check results."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.CheckTimeline.as_view()

    def test_no_results(self):
        """A check with no results should return no results."""
        check = factories.create_domain_check()
        url = reverse('status-timeline', kwargs={'check': check.pk})
        request = self.factory.get(url)
        response = self.view(request, check=check.pk)
        self.assertEqual(response.status_code, 200)

    def test_inactive(self):
        """Inactive checks should 404."""
        check = factories.create_domain_check(is_active=False)
        url = reverse('status-timeline', kwargs={'check': check.pk})
        request = self.factory.get(url)
        with self.assertRaises(Http404):
            self.view(request, check=check.pk)

    def test_get_results(self):
        """Build result dictionary from context."""
        view = views.CheckTimeline()
        view.request = Mock()
        view.args = []
        view.kwargs = {'check': 1}
        context = {
            'page_obj': Mock(object_list=[]),
            'paginator': Mock(count=0),
            'object_list': [],
        }
        result = view.get_results(context)
        self.assertEqual(result, {'count': 0, 'results': []})

    def test_render_response(self):
        """Response data should be returned as JSON."""
        check = factories.create_domain_check()
        success = factories.create_check_result(
            domain_check=check, status_code=200, response_time=0.1)
        failure = factories.create_check_result(
            domain_check=check, status_code=404, response_time=0.1)
        url = reverse('status-timeline', kwargs={'check': check.pk})
        request = self.factory.get(url)
        response = self.view(request, check=check.pk)
        self.assertEqual(response['Content-Type'], 'application/json')

        def convert_date(date):
            """Convert to ECMA-262 format."""
            result = date.isoformat()
            if date.microsecond:
                result = result[:23] + result[26:]
            if result.endswith('+00:00'):
                result = result[:-6] + 'Z'
            return result

        expected = [
            {
                'checked_on': convert_date(failure.checked_on),
                'status_code': failure.status_code,
                'response_time': failure.response_time,
            },
            {
                'checked_on': convert_date(success.checked_on),
                'status_code': success.status_code,
                'response_time': success.response_time,
            },
        ]
        self.assertJSONEqual(
            response.content.decode('utf-8'), {'count': 2, 'results': expected})
