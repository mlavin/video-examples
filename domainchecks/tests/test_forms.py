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
