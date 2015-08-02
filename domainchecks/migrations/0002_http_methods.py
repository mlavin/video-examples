# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domainchecks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domaincheck',
            name='method',
            field=models.CharField(default='get', choices=[('get', 'GET'), ('post', 'POST'), ('put', 'PUT'), ('delete', 'DELETE'), ('head', 'HEAD')], max_length=6),
        ),
    ]
