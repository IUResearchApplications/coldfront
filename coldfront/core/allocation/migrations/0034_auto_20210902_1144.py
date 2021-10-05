# Generated by Django 2.2.18 on 2021-09-02 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0033_auto_20210827_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='grand_challenge_program',
            field=models.CharField(blank=True, choices=[('healthinitiative', 'Precision Health Initiative'), ('envchange', 'Prepared for Environmental Change'), ('addiction', 'Responding to the Addiction Crisis')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='is_grand_challenge',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='grand_challenge_program',
            field=models.CharField(blank=True, choices=[('healthinitiative', 'Precision Health Initiative'), ('envchange', 'Prepared for Environmental Change'), ('addiction', 'Responding to the Addiction Crisis')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='is_grand_challenge',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
