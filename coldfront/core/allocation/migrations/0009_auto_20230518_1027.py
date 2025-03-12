# Generated by Django 3.2.14 on 2023-05-18 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0006_auto_20230518_1027'),
        ('allocation', '0008_auto_20230317_0811'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='allocation',
            options={'ordering': ['end_date'], 'permissions': (('can_view_all_allocations', 'Can view all allocations'), ('can_review_allocation_requests', 'Can review allocation requests'), ('can_manage_invoice', 'Can manage invoice'), ('can_remove_allocation', 'Can remove allocation'))},
        ),
        migrations.AddField(
            model_name='allocation',
            name='will_exceed_limit',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='allocationattributetype',
            name='linked_resources',
            field=models.ManyToManyField(blank=True, to='resource.Resource'),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='will_exceed_limit',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
    ]
