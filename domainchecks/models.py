from django.db import models


class ActiveManager(models.Manager):
    """Manager to exclude non-active records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


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
    METHOD_CHOICES = (
        (METHOD_GET, 'GET'),
        (METHOD_POST, 'POST'),
    )

    domain = models.CharField(max_length=253)
    path = models.CharField(max_length=1024)
    protocol = models.CharField(
        max_length=5, choices=PROTOCOL_CHOICES, default=PROTOCOL_HTTP)
    method = models.CharField(
        max_length=4, choices=METHOD_CHOICES, default=METHOD_GET)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return '{method} {url}'.format(
            method=self.get_method_display(), url=self.url)

    @property
    def url(self):
        return '{protocol}://{domain}{path}'.format(
            protocol=self.protocol, domain=self.domain, path=self.path)


class CheckResult(models.Model):
    """Result of a status check on a website."""

    domain_check = models.ForeignKey(DomainCheck)
    checked_on = models.DateTimeField()
    status_code = models.PositiveIntegerField(null=True)
    response_time = models.FloatField(null=True)
    response_body = models.TextField(default='')
