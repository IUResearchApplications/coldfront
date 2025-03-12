# Generated by Django 3.2.13 on 2022-07-21 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('resource', '0003_auto_20210817_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='review_groups',
            field=models.ManyToManyField(blank=True, related_name='review_groups_resource_set', to='auth.Group'),
        ),
    ]
