# Generated by Django 3.2.14 on 2023-01-09 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0004_resource_review_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalresourceattributetype',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resourceattributetype',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
