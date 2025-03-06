# Generated by Django 3.2.14 on 2023-05-18 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0005_auto_20230109_1134'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalresourceattribute',
            name='check_if_username_exists',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalresourceattribute',
            name='is_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalresourceattribute',
            name='resource_account_is_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resourceattribute',
            name='check_if_username_exists',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resourceattribute',
            name='is_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resourceattribute',
            name='resource_account_is_required',
            field=models.BooleanField(default=False),
        ),
    ]
