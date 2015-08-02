# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def create_domain_records(apps, schema_editor):
    Domain = apps.get_model('domainchecks', 'Domain')
    DomainCheck = apps.get_model('domainchecks', 'DomainCheck')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    checks = DomainCheck.objects.all()
    if checks.exists():
        owner = User.objects.order_by('pk').first()
        if owner is None:
            owner = User.objects.create_user('__dummy__', '', None)
        domains = {}
        for check in checks:
            check.domain_new = domains.get(check.domain)
            if check.domain_new is None:
                domain, _ = Domain.objects.get_or_create(
                    name=check.domain, defaults={'owner': owner})
                check.domain_new = domain
                domains[domain.name] = domain
            check.save(update_fields=('domain_new', ))


class Migration(migrations.Migration):

    dependencies = [
        ('domainchecks', '0004_new_domain'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_domain_records),
        migrations.AlterField(
            model_name='domaincheck',
            name='domain_new',
            field=models.ForeignKey(to='domainchecks.Domain'),
        ),
    ]
