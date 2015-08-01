import django_filters

from django import forms

from . import models


class CheckFilterForm(forms.Form):
    """Additional filter validations."""

    def clean(self):
        cleaned_data = self.cleaned_data
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start is not None and end is not None:
            if start > end:
                raise forms.ValidationError(
                    'End date must be greater than start date.')
            elif (end - start).total_seconds() > 60 * 60 * 24:
                raise forms.ValidationError(
                    'Start to end must be less than one day.')
        return cleaned_data


class CheckResultFilter(django_filters.FilterSet):
    """Filter check results for a time range."""

    start = django_filters.DateTimeFilter(
        name='checked_on', lookup_type='gte', required=True)
    end = django_filters.DateTimeFilter(
        name='checked_on', lookup_type='lte', required=True)

    class Meta:
        model = models.CheckResult
        form = CheckFilterForm
        order_by = ('-checked_on', )
