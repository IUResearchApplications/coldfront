# Generated by Django 2.2.18 on 2021-07-15 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0003_auto_20191018_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='leverage_multi_gpu_decision',
            field=models.CharField(default='No', max_length=3),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='leverage_multi_gpu_decision',
            field=models.CharField(default='No', max_length=3),
        ),
    ]
