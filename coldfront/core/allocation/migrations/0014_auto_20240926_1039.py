# Generated by Django 3.2.14 on 2024-09-26 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0013_auto_20240822_1035'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allocationattributetype',
            name='linked_allocation_attribute',
        ),
        migrations.RemoveField(
            model_name='historicalallocationattributetype',
            name='linked_allocation_attribute',
        ),
    ]
