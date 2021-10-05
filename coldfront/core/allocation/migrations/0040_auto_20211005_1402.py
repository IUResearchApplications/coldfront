# Generated by Django 2.2.18 on 2021-10-05 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0039_auto_20210910_0938'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allocation',
            name='campus_affiliation',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='email',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='faculty_email',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='project_directory_name',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='storage_space_with_unit',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='store_ephi',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='total_cost',
        ),
        migrations.RemoveField(
            model_name='allocation',
            name='url',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='campus_affiliation',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='email',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='faculty_email',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='project_directory_name',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='storage_space_with_unit',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='store_ephi',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='total_cost',
        ),
        migrations.RemoveField(
            model_name='historicalallocation',
            name='url',
        ),
        migrations.AlterField(
            model_name='allocation',
            name='storage_space',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='historicalallocation',
            name='storage_space',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
