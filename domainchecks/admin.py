from django.contrib import admin
from django.utils.timesince import timesince

from . import models


class StatusListFilter(admin.SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('unknown', 'Unknown'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


@admin.register(models.DomainCheck)
class DomainCheckAdmin(admin.ModelAdmin):

    list_display = (
        'domain', 'path', 'protocol', 'method', 'is_active',
        'status', 'last_checked', )
    list_filter = ('protocol', 'method', StatusListFilter, 'is_active', )
    search_fields = ('domain', )
    actions = ('run_check', )

    def get_queryset(self, request):
        return super().get_queryset(request).status()

    def status(self, obj):
        return obj.status.title()
    status.admin_order_field = 'success_rate'

    def last_checked(self, obj):
        if obj.last_check:
            return '{} ago'.format(timesince(obj.last_check))
        else:
            return 'Never'
    last_checked.admin_order_field = 'last_check'

    def run_check(self, request, queryset):
        for item in queryset:
            item.run_check()
    run_check.short_description = 'Run the domain check'


@admin.register(models.CheckResult)
class CheckResultAdmin(admin.ModelAdmin):

    date_hierarchy = 'checked_on'
    list_display = ('domain_check', 'status_code', )
    list_filter = ('checked_on', )
