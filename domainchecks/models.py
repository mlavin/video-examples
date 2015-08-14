import datetime
import time

import requests

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Case, Count, F, Max, Q, Value, When
from django.utils.timezone import now


class DomainCheckQuerySet(models.QuerySet):
    """Custom queryset to filter and annotate domain checks."""

    def active(self):
        return self.filter(is_active=True)

    def stale(self, cutoff=datetime.timedelta(hours=1)):
        end_time = now() - cutoff
        return self.annotate(
            last_check=Max('checkresult__checked_on')
        ).filter(
            Q(last_check__lt=end_time) | Q(last_check__isnull=True))

    def status(self, cutoff=datetime.timedelta(hours=1)):
        start_time = now() - cutoff
        ping = Q(checkresult__checked_on__gte=start_time)
        success = Q(
            checkresult__checked_on__gte=start_time,
            checkresult__status_code__range=(200, 299))
        return self.annotate(
            last_check=Max('checkresult__checked_on'),
            successes=Count(Case(When(success, then=1))),
            pings=Count(Case(When(ping, then=1))),
        ).annotate(
            success_rate=F('successes') * 100.0 / F('pings')
        ).annotate(
            status=Case(
                When(success_rate__gt=90, then=Value('good')),
                When(success_rate__range=(75, 90), then=Value('fair')),
                When(success_rate__lt=75, then=Value('poor')),
                When(success_rate__isnull=True, then=Value('unknown')),
                output_field=models.CharField())
        )


class Domain(models.Model):
    """Domain managed by a user."""

    name = models.CharField(max_length=253, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('status-detail', kwargs={'domain': self.name})


class DomainCheck(models.Model):
    """Configured website check."""

    PROTOCOL_HTTP = 'http'
    PROTOCOL_HTTPS = 'https'

    PROTOCOL_CHOICES = (
        (PROTOCOL_HTTP, 'HTTP'),
        (PROTOCOL_HTTPS, 'HTTPS'),
    )

    METHOD_GET = 'get'
    METHOD_POST = 'post'
    METHOD_PUT = 'put'
    METHOD_DELETE = 'delete'
    METHOD_HEAD = 'head'

    METHOD_CHOICES = (
        (METHOD_GET, 'GET'),
        (METHOD_POST, 'POST'),
        (METHOD_PUT, 'PUT'),
        (METHOD_DELETE, 'DELETE'),
        (METHOD_HEAD, 'HEAD'),
    )

    domain = models.ForeignKey(Domain)
    path = models.CharField(max_length=1024)
    protocol = models.CharField(
        max_length=5, choices=PROTOCOL_CHOICES, default=PROTOCOL_HTTP)
    method = models.CharField(
        max_length=6, choices=METHOD_CHOICES, default=METHOD_GET)
    is_active = models.BooleanField(default=True)

    objects = DomainCheckQuerySet.as_manager()

    def __str__(self):
        return '{method} {url}'.format(
            method=self.get_method_display(), url=self.url)

    @property
    def url(self):
        return '{protocol}://{domain}{path}'.format(
            protocol=self.protocol, domain=self.domain, path=self.path)

    def run_check(self, timeout=10):
        start = time.time()
        result = CheckResult(domain_check=self, checked_on=now())
        try:
            response = requests.request(
                self.method, self.url, allow_redirects=False, timeout=timeout)
            result.status_code = response.status_code
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            # Host could not be resolved or the connection was refused
            pass
        except requests.exceptions.Timeout:
            # Request timed out
            pass
        except requests.exceptions.RequestException:
            # Server responded with 4XX or 5XX status code
            result.response_body = response.text
        else:
            result.response_body = response.text
        finally:
            result.response_time = time.time() - start
            result.save()


class CheckResult(models.Model):
    """Result of a status check on a website."""

    domain_check = models.ForeignKey(DomainCheck)
    checked_on = models.DateTimeField()
    status_code = models.PositiveIntegerField(null=True)
    response_time = models.FloatField(null=True)
    response_body = models.TextField(default='')
