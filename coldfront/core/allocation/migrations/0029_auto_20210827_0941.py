# Generated by Django 2.2.18 on 2021-08-27 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0028_auto_20210826_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='department_full_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='department_short_name',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='primary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='secondary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='department_full_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='department_short_name',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='primary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='secondary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
