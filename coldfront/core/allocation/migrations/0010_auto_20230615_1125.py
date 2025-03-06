# Generated by Django 3.2.14 on 2023-06-15 15:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0006_auto_20230518_1027'),
        ('allocation', '0009_auto_20230518_1027'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocationattributetype',
            name='linked_resource_attribute_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='resource.resourceattributetype'),
        ),
        migrations.AddField(
            model_name='historicalallocationattributetype',
            name='linked_resource_attribute_type',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.resourceattributetype'),
        ),
    ]
