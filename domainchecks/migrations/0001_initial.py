# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CheckResult',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('checked_on', models.DateTimeField()),
                ('status_code', models.PositiveIntegerField(null=True)),
                ('response_time', models.FloatField(null=True)),
                ('response_body', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='DomainCheck',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('domain', models.CharField(max_length=253)),
                ('path', models.CharField(max_length=1024)),
                ('protocol', models.CharField(default='http', max_length=5, choices=[('http', 'HTTP'), ('https', 'HTTPS')])),
                ('method', models.CharField(default='get', max_length=4, choices=[('get', 'GET'), ('post', 'POST')])),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='checkresult',
            name='domain_check',
            field=models.ForeignKey(to='domainchecks.DomainCheck'),
        ),
    ]
