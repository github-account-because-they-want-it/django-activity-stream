# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actstream', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='seen',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
