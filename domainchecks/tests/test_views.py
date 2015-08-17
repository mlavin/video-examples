import datetime

from unittest.mock import Mock

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import RequestFactory, TestCase

from .. import models, views
from . import factories


class StatusListViewTestCase(TestCase):
    """Listing all active domains."""

    def setUp(self):
        self.url = reverse('status-list')
        self.factory = RequestFactory()
        self.view = views.StatusList.as_view()
        self.user = factories.create_user(password='test')

    def test_render_domains(self):
        """Page should render all active domains."""
        example = factories.create_domain(name='example.com', owner=self.user)
        factories.create_domain_check(domain=example)
        dj = factories.create_domain(name='djangoproject.com', owner=self.user)
        factories.create_domain_check(domain=dj)
        evil = factories.create_domain(name='evil.com', owner=self.user)
        factories.create_domain_check(domain=evil, is_active=False)
        other = factories.create_domain(name='other.com')
        factories.create_domain_check(domain=other)
        with self.assertTemplateUsed('domainchecks/status-list.html'):
            self.client.login(username=self.user.username, password='test')
            response = self.client.get(self.url)
            self.assertContains(response, 'example.com')
            self.assertContains(response, 'djangoproject.com')
            self.assertNotContains(response, 'evil.com')
            self.assertNotContains(response, other.name)

    def test_no_domains(self):
        """Page will still render if there are no domains."""
        request = self.factory.get(self.url)
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated(self):
        """Handle unautenticated users."""
        request = self.factory.get(self.url)
        request.user = Mock()
        request.user.is_authenticated.return_value = False
        response = self.view(request)
        self.assertEqual(response.status_code, 200)


class StatusDetailViewTestCase(TestCase):
    """All checks for a single active domain: public view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.StatusDetail.as_view()

    def test_no_checks_found(self):
        """Page should 404 if there are no checks for a given domain."""
        url = reverse('public-status-detail', kwargs={'domain': 'unknown.com'})
        request = self.factory.get(url)
        with self.assertRaises(Http404):
            self.view(request, domain='unknown.com')

    def test_no_active_checks(self):
        """Page should 404 if there are no active checks for the domain."""
        check = factories.create_domain_check(is_active=False)
        url = reverse('public-status-detail', kwargs={'domain': check.domain.name})
        request = self.factory.get(url)
        with self.assertRaises(Http404):
            self.view(request, domain=check.domain.name)

    def test_query_matched_domain(self):
        """Checks should be filtered to the requested domain."""
        check = factories.create_domain_check()
        factories.create_domain_check(domain='other.com')
        url = reverse('public-status-detail', kwargs={'domain': check.domain.name})
        view = views.StatusDetail()
        view.request = self.factory.get(url)
        view.args = []
        view.kwargs = {'domain': check.domain.name}
        qs = view.get_queryset()
        self.assertQuerysetEqual(
            qs, [check.pk, ], transform=lambda x: x.pk)

    def test_render_checks(self):
        """Render the active checks for a given domain."""
        check = factories.create_domain_check()
        factories.create_domain_check(
            domain=check.domain, path='/extra/')
        url = reverse('public-status-detail', kwargs={'domain': check.domain.name})
        with self.assertTemplateUsed('domainchecks/status-detail.html'):
            response = self.client.get(url)
            self.assertContains(response, 'HTTP GET /')
            self.assertContains(response, 'HTTP GET /extra/')


class PrivateStatusDetailViewTestCase(TestCase):
    """All checks for a single active domain: owner view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.PrivateStatusDetail.as_view()
        self.user = factories.create_user(password='test')

    def test_no_checks_found(self):
        """Page should 404 if there are no checks for a given domain."""
        url = reverse('status-detail', kwargs={'domain': 'unknown.com'})
        request = self.factory.get(url)
        request.user = self.user
        with self.assertRaises(Http404):
            self.view(request, domain='unknown.com')

    def test_no_active_checks(self):
        """Page should 404 if there are no active checks for the domain."""
        domain = factories.create_domain(owner=self.user)
        factories.create_domain_check(domain=domain, is_active=False)
        url = reverse('status-detail', kwargs={'domain': domain.name})
        request = self.factory.get(url)
        request.user = self.user
        with self.assertRaises(Http404):
            self.view(request, domain=domain.name)

    def test_query_matched_domain(self):
        """Checks should be filtered to the requested domain."""
        domain = factories.create_domain(owner=self.user)
        check = factories.create_domain_check(domain=domain)
        factories.create_domain_check(domain='other.com')
        url = reverse('status-detail', kwargs={'domain': domain.name})
        view = views.StatusDetail()
        view.request = self.factory.get(url)
        view.args = []
        view.kwargs = {'domain': domain.name}
        qs = view.get_queryset()
        self.assertQuerysetEqual(
            qs, [check.pk, ], transform=lambda x: x.pk)

    def test_render_checks(self):
        """Render the active checks for a given domain."""
        domain = factories.create_domain(owner=self.user)
        check = factories.create_domain_check(domain=domain)
        factories.create_domain_check(
            domain=check.domain, path='/extra/')
        url = reverse('status-detail', kwargs={'domain': domain.name})
        with self.assertTemplateUsed('domainchecks/status-detail.html'):
            self.client.login(username=self.user.username, password='test')
            response = self.client.get(url)
            self.assertContains(response, 'HTTP GET /')
            self.assertContains(response, 'HTTP GET /extra/')

    def test_not_owner(self):
        """Other users should not have permission to see this view."""
        domain = factories.create_domain(owner=self.user)
        factories.create_domain_check(domain=domain, is_active=False)
        url = reverse('status-detail', kwargs={'domain': domain.name})
        request = self.factory.get(url)
        request.user = factories.create_user()
        with self.assertRaises(PermissionDenied):
            self.view(request, domain=domain.name)


class CheckTimelineViewTestCase(TestCase):
    """JSON list of check results."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.CheckTimeline.as_view()

    def test_no_results(self):
        """A check with no results should return no results."""
        check = factories.create_domain_check()
        url = reverse('status-timeline', kwargs={'check': check.pk})
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        data = {
            'start': yesterday.isoformat(sep=' '),
            'end': today.isoformat(sep=' '),
        }
        request = self.factory.get(url, data=data)
        response = self.view(request, check=check.pk)
        self.assertEqual(response.status_code, 200)

    def test_no_range(self):
        """The start and end range are required."""
        check = factories.create_domain_check()
        url = reverse('status-timeline', kwargs={'check': check.pk})
        request = self.factory.get(url)
        response = self.view(request, check=check.pk)
        self.assertEqual(response.status_code, 400)

    def test_invalid_range(self):
        """Handle an invalid range."""
        check = factories.create_domain_check()
        url = reverse('status-timeline', kwargs={'check': check.pk})
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        data = {
            'start': today.isoformat(sep=' '),
            'end': yesterday.isoformat(sep=' '),
        }
        request = self.factory.get(url, data=data)
        response = self.view(request, check=check.pk)
        self.assertEqual(response.status_code, 400)

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
            'object_list': [],
        }
        result = view.get_results(context)
        self.assertEqual(result, {'results': []})

    def test_render_response(self):
        """Response data should be returned as JSON."""
        check = factories.create_domain_check()
        success = factories.create_check_result(
            domain_check=check, status_code=200, response_time=0.1)
        failure = factories.create_check_result(
            domain_check=check, status_code=404, response_time=0.1)
        url = reverse('status-timeline', kwargs={'check': check.pk})
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        data = {
            'start': yesterday.isoformat(sep=' '),
            'end': today.isoformat(sep=' '),
        }
        request = self.factory.get(url, data=data)
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
            response.content.decode('utf-8'), {'results': expected})


class CreateDomainViewTestCase(TestCase):
    """Adding new domains."""

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('domain-add')
        self.view = views.CreateDomain.as_view()
        self.user = factories.create_user(password='test')

    def get_valid_data(self, checks=1):
        result = self.get_form_data()
        result.update(self.get_formset_data(checks=checks))
        return result

    def get_form_data(self):
        return {'name': 'example.com'}

    def get_formset_data(self, checks=1):
        data = {
            'checks-TOTAL_FORMS': '3',
            'checks-INITIAL_FORMS': '0',
            'checks-MIN_NUM_FORMS': '1',
            'checks-MAX_NUM_FORMS': '3',
        }
        for i in range(3):
            data.update({
                'checks-{}-protocol'.format(i): 'http',
                'checks-{}-path'.format(i): '/{}/'.format(i) if i < checks else '',
                'checks-{}-method'.format(i): 'get',
                'checks-{}-is_active'.format(i): 'on',
                'checks-{}-id'.format(i): '',
                'checks-{}-domain'.format(i): '',
            })
        return data

    def test_render_form(self):
        """Fetch page to render the form."""
        self.client.login(username=self.user.username, password='test')
        with self.assertTemplateUsed('domainchecks/domain-form.html'):
            response = self.client.get(self.url)
            self.assertContains(
                response,
                '<input id="id_name" maxlength="253" name="name" type="text">',
                html=True)

    def test_domain_created(self):
        """Submitting valid data should create a new domain."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request)
        domain = models.Domain.objects.latest('pk')
        self.assertEqual(domain.name, 'example.com')
        self.assertEqual(domain.owner, self.user)

    def test_form_redirect(self):
        """Submit valid data and check the redirect."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/domains/example.com/')

    def test_invalid_data(self):
        """Handle invalid form submission."""
        data = self.get_valid_data()
        data['name'] = ''
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        response = self.view(request)
        self.assertContains(response, 'This field is required.')

    def test_check_create(self):
        """Related domain checks should also be created for the domain."""
        data = self.get_valid_data(checks=2)
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request)
        domain = models.Domain.objects.latest('pk')
        checks = domain.domaincheck_set.all()
        self.assertEqual(checks.count(), 2)

    def test_checks_required(self):
        """At least on domain check is required."""
        data = self.get_valid_data(checks=1)
        data['checks-0-path'] = ''
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        response = self.view(request)
        self.assertContains(response, 'This field is required.')


class EditDomainViewTestCase(TestCase):
    """Update an existing domain."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.EditDomain.as_view()
        self.user = factories.create_user(password='test')
        self.domain = factories.create_domain(owner=self.user)
        self.check = factories.create_domain_check(domain=self.domain)
        self.url = reverse('domain-edit', kwargs={'domain': self.domain.name})

    def get_valid_data(self):
        result = self.get_form_data()
        result.update(self.get_formset_data())
        return result

    def get_form_data(self):
        return {'name': self.domain.name}

    def get_formset_data(self):
        checks = self.domain.domaincheck_set.all()
        existing = checks.count()
        data = {
            'checks-TOTAL_FORMS': '3',
            'checks-INITIAL_FORMS': existing,
            'checks-MIN_NUM_FORMS': '1',
            'checks-MAX_NUM_FORMS': '3',
        }
        for i in range(3):
            if i < existing:
                check = checks[i]
                data.update({
                    'checks-{}-protocol'.format(i): check.protocol,
                    'checks-{}-path'.format(i): check.path,
                    'checks-{}-method'.format(i): check.method,
                    'checks-{}-is_active'.format(i): 'on' if check.is_active else '',
                    'checks-{}-id'.format(i): check.pk,
                    'checks-{}-domain'.format(i): self.domain.pk,
                })
            else:
                data.update({
                    'checks-{}-protocol'.format(i): 'http',
                    'checks-{}-path'.format(i): '',
                    'checks-{}-method'.format(i): 'get',
                    'checks-{}-is_active'.format(i): 'on',
                    'checks-{}-id'.format(i): '',
                    'checks-{}-domain'.format(i): self.domain.pk,
                })
        return data

    def test_render_form(self):
        """Get the page and render the form."""
        self.client.login(username=self.user.username, password='test')
        with self.assertTemplateUsed('domainchecks/domain-form.html'):
            response = self.client.get(self.url)
            field = (
                '<input id="id_name" maxlength="253"'
                ' name="name" type="text" value="{}">'
            ).format(self.domain.name)
            self.assertContains(response, field, html=True)

    def test_domain_updated(self):
        """Update domain data on submit."""
        data = self.get_valid_data()
        data['name'] = 'example.com'
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request, domain=self.domain.name)
        self.domain.refresh_from_db()
        self.assertEqual(self.domain.name, 'example.com')
        self.assertEqual(self.domain.owner, self.user)

    def test_form_redirect(self):
        """Redirect to the domain url on submit."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        response = self.view(request, domain=self.domain.name)
        self.domain.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.domain.get_absolute_url())

    def test_invalid_data(self):
        """Render form errors on submit."""
        data = self.get_valid_data()
        data['name'] = ''
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        response = self.view(request, domain=self.domain.name)
        self.assertContains(response, 'This field is required.')

    def test_domain_does_not_exist(self):
        """Handle domain name which doesn't exist."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        with self.assertRaises(Http404):
            self.view(request, domain='does.not.exist')

    def test_not_owner(self):
        """User should not be able to edit domain if they are not the owner."""
        data = self.get_valid_data()
        request = self.factory.post(self.url, data=data)
        request.user = factories.create_user()
        with self.assertRaises(PermissionDenied):
            self.view(request, domain=self.domain.name)

    def test_owner_not_edittable(self):
        """User should not be able to change the owner."""
        other = factories.create_user()
        data = self.get_valid_data()
        data['name'] = 'example.com'
        data['owner'] = other.pk
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request, domain=self.domain.name)
        self.domain.refresh_from_db()
        self.assertEqual(self.domain.name, 'example.com')
        self.assertEqual(self.domain.owner, self.user)

    def test_create_new_checks(self):
        """New paths to check can be added for the domain."""
        data = self.get_valid_data()
        data['checks-1-path'] = '/new/'
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request, domain=self.domain.name)
        checks = self.domain.domaincheck_set.all()
        self.assertEqual(checks.count(), 2)
        self.assertEqual(checks[1].path, '/new/')

    def test_checks_edittable(self):
        """Related checks should be edittable as well."""
        data = self.get_valid_data()
        data['checks-0-path'] = '/test/'
        request = self.factory.post(self.url, data=data)
        request.user = self.user
        self.view(request, domain=self.domain.name)
        self.check.refresh_from_db()
        self.assertEqual(self.check.path, '/test/')
