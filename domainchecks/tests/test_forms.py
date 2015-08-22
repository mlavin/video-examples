import datetime

from unittest.mock import Mock

from django.test import TestCase
from django.utils.timezone import now

from .. import forms, models
from . import factories


class CheckResultFilterTestCase(TestCase):
    """Filtering status results to a date range."""

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    def test_valid_range(self):
        """Filter on valid start/end range."""
        data = {
            'start': self.yesterday.isoformat(),
            'end': self.today.isoformat(),
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertTrue(result.form.is_valid())

    def test_valid_range_datetimes(self):
        """Filter on valid start/end range including time."""
        data = {
            'start': datetime.datetime.combine(
                self.yesterday, datetime.time(0, 0, 0)).isoformat(sep=' '),
            'end': datetime.datetime.combine(
                self.yesterday, datetime.time(12, 0, 0)).isoformat(sep=' '),
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertTrue(result.form.is_valid())

    def test_invalid_range(self):
        """End date must be greater than the start date."""
        data = {
            'start': self.today.isoformat(),
            'end': self.yesterday.isoformat(),
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertFalse(result.form.is_valid())

    def test_range_too_long(self):
        """End and start must be less than a day apart."""
        data = {
            'start': self.yesterday.isoformat(),
            'end': self.tomorrow.isoformat(),
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertFalse(result.form.is_valid())

    def test_missing_start(self):
        """Start date must be given."""
        data = {
            'start': '',
            'end': self.today.isoformat(),
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertFalse(result.form.is_valid())

    def test_missing_end(self):
        """End date must be given."""
        data = {
            'start': self.yesterday.isoformat(),
            'end': '',
        }
        qs = Mock()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertFalse(result.form.is_valid())

    def test_functional(self):
        """Functional test of filtering a queryset."""
        check = factories.create_domain_check()
        current_time = now().replace(microsecond=0)
        for i in range(10):
            factories.create_check_result(
                domain_check=check,
                checked_on=current_time - datetime.timedelta(hours=i))
        middle = current_time - datetime.timedelta(hours=5)
        data = {
            'start': middle.replace(tzinfo=None).isoformat(sep=' '),
            'end': current_time.replace(tzinfo=None).isoformat(sep=' ')
        }
        qs = models.CheckResult.objects.all()
        result = forms.CheckResultFilter(data=data, queryset=qs)
        self.assertEqual(result.count(), 6)


class DomainFormTestCase(TestCase):
    """Validation of domains and related checks."""

    def get_form(self, instance=None, data=None):
        return forms.DomainForm(data=data, instance=instance)

    def test_valid_new_domain(self):
        """Minimal valid new domain."""
        data = factories.build_domain_form_data(domain=None)
        form = self.get_form(instance=None, data=data)
        self.assertTrue(form.is_valid())

    def test_valid_edit_domain(self):
        """Minimal valid domain edit."""
        domain = factories.create_domain_check().domain
        data = factories.build_domain_form_data(domain=domain)
        form = self.get_form(instance=domain, data=data)
        self.assertTrue(form.is_valid())

    def test_check_required(self):
        """At least one check must be given."""
        data = factories.build_domain_form_data(domain=None)
        data['checks-0-path'] = ''
        form = self.get_form(instance=None, data=data)
        self.assertFalse(form.is_valid())

    def test_active_check_required(self):
        """A new domain must have at least one active check."""
        data = factories.build_domain_form_data(domain=None)
        data['checks-0-is_active'] = ''
        form = self.get_form(instance=None, data=data)
        self.assertFalse(form.is_valid())

    def test_check_required_edit(self):
        """On edit, the domain must have at least one active check."""
        domain = factories.create_domain_check().domain
        data = factories.build_domain_form_data(domain=domain)
        data['checks-0-is_active'] = ''
        form = self.get_form(instance=domain, data=data)
        self.assertFalse(form.is_valid())

    def test_name_unique(self):
        """Domain name must be unique."""
        domain = factories.create_domain()
        data = factories.build_domain_form_data(domain=None)
        data['name'] = domain.name
        form = self.get_form(instance=None, data=data)
        self.assertFalse(form.is_valid())

    def test_save_new(self):
        """Save a newly create domain and its checks."""
        data = factories.build_domain_form_data(domain=None)
        data['name'] = 'new.com'
        form = self.get_form(instance=None, data=data)
        # Owner must be set before it can be saved
        form.instance.owner = factories.create_user()
        domain = form.save()
        self.assertEqual(domain.name, 'new.com')
        self.assertEqual(domain.domaincheck_set.all().count(), 1)

    def test_save_updates(self):
        """Update an exist domain/checks."""
        check = factories.create_domain_check()
        domain = check.domain
        data = factories.build_domain_form_data(domain=domain)
        data['name'] = 'edit.com'
        form = self.get_form(instance=domain, data=data)
        result = form.save()
        self.assertEqual(result.pk, domain.pk)
        self.assertEqual(result.name, 'edit.com')
        self.assertEqual(domain.domaincheck_set.all().count(), 1)
