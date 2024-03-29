# -*- coding: utf-8 -*-
# Generated by Django 4.2.2 on 2024-03-04 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("signature_validator", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pdfdocumentvalidator",
            name="all_signers_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="pdfdocumentvalidator",
            name="distinct_people_signed",
            field=models.IntegerField(default=0),
        ),
    ]
