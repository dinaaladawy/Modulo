# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-30 05:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo', '0011_auto_20170330_0615'),
    ]

    operations = [
        migrations.RenameField(
            model_name='module',
            old_name='place',
            new_name='location',
        ),
    ]
