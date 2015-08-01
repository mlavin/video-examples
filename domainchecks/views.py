from django.http import JsonResponse
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .forms import CheckResultFilter
from .models import DomainCheck, CheckResult


class StatusList(ListView):
    queryset = DomainCheck.objects.active().values('domain').status().order_by('domain')
    template_name = 'domainchecks/status-list.html'
    context_object_name = 'domains'


class StatusDetail(ListView):
    template_name = 'domainchecks/status-detail.html'
    allow_empty = False
    context_object_name = 'checks'

    def get_queryset(self):
        return DomainCheck.objects.active().filter(
            domain=self.kwargs['domain']).status().order_by('path')


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
