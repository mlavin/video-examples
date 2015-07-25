from django.views.generic import ListView

from .models import DomainCheck


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
