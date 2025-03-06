# Generated by Django 4.2.11 on 2025-02-19 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0010_alter_projectadminaction_action'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ['title'], 'permissions': (('can_view_all_projects', 'Can view all projects'), ('can_review_pending_projects', 'Can review pending project requests/reviews'))},
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='max_managers',
            field=models.IntegerField(default=3),
        ),
        migrations.AlterField(
            model_name='project',
            name='max_managers',
            field=models.IntegerField(default=3),
        ),
    ]
