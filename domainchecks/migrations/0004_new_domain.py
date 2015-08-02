# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domainchecks', '0003_domain_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='domaincheck',
            name='domain_new',
            field=models.ForeignKey(null=True, to='domainchecks.Domain'),
        ),
    ]
