# Generated by Django 2.2.18 on 2021-07-29 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0012_auto_20210729_1016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allocation',
            name='leverage_multiple_gpus',
            field=models.CharField(choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='historicalallocation',
            name='leverage_multiple_gpus',
            field=models.CharField(choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
    ]
