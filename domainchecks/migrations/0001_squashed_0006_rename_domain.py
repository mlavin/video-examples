# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckResult',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('checked_on', models.DateTimeField()),
                ('status_code', models.PositiveIntegerField(null=True)),
                ('response_time', models.FloatField(null=True)),
                ('response_body', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='DomainCheck',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('path', models.CharField(max_length=1024)),
                ('protocol', models.CharField(choices=[('http', 'HTTP'), ('https', 'HTTPS')], max_length=5, default='http')),
                ('method', models.CharField(choices=[('get', 'GET'), ('post', 'POST'), ('put', 'PUT'), ('delete', 'DELETE'), ('head', 'HEAD')], max_length=6, default='get')),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='checkresult',
            name='domain_check',
            field=models.ForeignKey(to='domainchecks.DomainCheck'),
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=253, unique=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='domaincheck',
            name='domain',
            field=models.ForeignKey(to='domainchecks.Domain'),
        ),
    ]
