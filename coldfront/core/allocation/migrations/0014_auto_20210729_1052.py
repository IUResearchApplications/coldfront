# Generated by Django 2.2.18 on 2021-07-29 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0013_auto_20210729_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='for_coursework',
            field=models.CharField(choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='for_coursework',
            field=models.CharField(choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
    ]
