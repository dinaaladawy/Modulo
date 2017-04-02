# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-02 07:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo', '0013_auto_20170401_2105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='exam_type',
            field=models.CharField(default=None, max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='location',
            name='location',
            field=models.CharField(default=None, max_length=500, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='module',
            name='exam',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='modulo.Exam'),
        ),
        migrations.AlterField(
            model_name='module',
            name='location',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='modulo.Location'),
        ),
    ]