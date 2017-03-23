# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 06:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo', '0007_auto_20170316_0937'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Interests',
            new_name='Interest',
        ),
        migrations.AlterField(
            model_name='module',
            name='exam',
            field=models.IntegerField(choices=[(0, 'Written exam'), (1, 'Oral exam'), (3, 'Assessed/continuous assessment'), (4, '')], default=4),
        ),
    ]