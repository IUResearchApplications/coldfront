# Generated by Django 2.2.18 on 2021-08-27 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0029_auto_20210827_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='use_indefinitely',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='use_indefinitely',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
