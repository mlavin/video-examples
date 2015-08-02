# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domainchecks', '0005_populate_new_domain'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='domaincheck',
            name='domain',
        ),
        migrations.RenameField(
            model_name='domaincheck',
            old_name='domain_new',
            new_name='domain',
        ),
    ]
