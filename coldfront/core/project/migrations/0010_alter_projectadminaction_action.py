# Generated by Django 4.2.11 on 2025-01-21 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0009_alter_project_description_alter_project_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectadminaction',
            name='action',
            field=models.CharField(max_length=256),
        ),
    ]
