# Generated by Django 2.2.18 on 2021-08-17 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0019_auto_20210817_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allocation',
            name='system',
            field=models.CharField(choices=[('Carbonate', 'Carbonate'), ('BigRed3', 'Big Red 3')], max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='historicalallocation',
            name='system',
            field=models.CharField(choices=[('Carbonate', 'Carbonate'), ('BigRed3', 'Big Red 3')], max_length=9, null=True),
        ),
    ]
