import django_filters

from django import forms
from django.forms.models import BaseInlineFormSet, inlineformset_factory

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


class BaseDomainCheckFormSet(BaseInlineFormSet):
    """Additional validations for required domain checks."""

    def clean(self):
        super().clean()
        active = 0
        for form in self.forms:
            if form.is_valid() and form not in self.deleted_forms:
                if form.cleaned_data.get('is_active', False):
                    active += 1
        if active == 0:
            msg = 'A domain must have at least one active check.'
            raise forms.ValidationError(msg)


DomainCheckFormSet = inlineformset_factory(
    parent_model=models.Domain, model=models.DomainCheck,
    fields=('protocol', 'path', 'method', 'is_active', ),
    formset=BaseDomainCheckFormSet,
    extra=3, can_delete=False,
    max_num=3, validate_max=True,
    min_num=1, validate_min=True,
)


class DomainForm(forms.ModelForm):
    """Form to allow users to create/edit their own domains."""

    class Meta:
        model = models.Domain
        fields = ('name', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checks = DomainCheckFormSet(
            instance=self.instance, prefix='checks',
            data=self.data if self.is_bound else None)

    def is_valid(self):
        domain_valid = super().is_valid()
        checks_valid = self.checks.is_valid()
        return domain_valid and checks_valid

    def save(self, commit=True):
        domain = super().save(commit=commit)
        domain._checks = self.checks.save(commit=commit)
        return domain
