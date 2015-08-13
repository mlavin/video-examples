from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .forms import CheckResultFilter
from .models import Domain, DomainCheck, CheckResult


class StatusList(ListView):
    template_name = 'domainchecks/status-list.html'
    context_object_name = 'domains'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return DomainCheck.objects.active().filter(
                domain__owner=self.request.user
            ).values('domain__name').status().order_by('domain__name')
        else:
            return DomainCheck.objects.none()


class StatusDetail(ListView):
    template_name = 'domainchecks/public-status-detail.html'
    allow_empty = False
    context_object_name = 'checks'

    def get_queryset(self):
        return DomainCheck.objects.active().filter(
            domain__name=self.kwargs['domain']).status().order_by('path')


class PrivateStatusDetail(StatusDetail):
    template_name = 'domainchecks/status-detail.html'

    def get_queryset(self):
        domain = get_object_or_404(Domain, name=self.kwargs['domain'])
        if domain.owner != self.request.user:
            raise PermissionDenied('Must be the domain owner to view this page.')
        return super().get_queryset()


class CheckTimeline(ListView):

    def get_queryset(self):
        check = get_object_or_404(
            DomainCheck.objects.active(), pk=self.kwargs['check'])
        qs = CheckResult.objects.filter(domain_check=check)
        results = CheckResultFilter(self.request.GET, queryset=qs, strict=True)
        self._filters_valid = results.form.is_valid()
        return results.qs.values('checked_on', 'response_time', 'status_code')

    def render_to_response(self, context, **response_kwargs):
        results = self.get_results(context)
        if not getattr(self, '_filters_valid', False):
            response_kwargs['status'] = 400
        return JsonResponse(results, **response_kwargs)

    def get_results(self, context):
        results = list(context['object_list'])
        return {
            'results': results,
        }
