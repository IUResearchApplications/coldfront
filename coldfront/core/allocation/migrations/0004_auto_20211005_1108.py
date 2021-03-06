# Generated by Django 2.2.18 on 2021-10-05 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0003_auto_20191018_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocation',
            name='access_level',
            field=models.CharField(blank=True, choices=[('Masked', 'Masked'), ('Unmasked', 'Unmasked')], max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='account_number',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='applications_list',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='confirm_understanding',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='data_management_plan',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='department_full_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='department_short_name',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='devices_ip_addresses',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='dl_workflow',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='fiscal_officer',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='for_coursework',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
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
            model_name='allocation',
            name='it_pros',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='leverage_multiple_gpus',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='phi_association',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='primary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='secondary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='storage_space',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='sub_account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='system',
            field=models.CharField(blank=True, choices=[('Carbonate', 'Carbonate'), ('BigRed3', 'Big Red 3')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='training_or_inference',
            field=models.CharField(blank=True, choices=[('Training', 'Training'), ('Inference', 'Inference'), ('Both', 'Both')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='use_indefinitely',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='access_level',
            field=models.CharField(blank=True, choices=[('Masked', 'Masked'), ('Unmasked', 'Unmasked')], max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='account_number',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='applications_list',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='confirm_understanding',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='data_management_plan',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='department_full_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='department_short_name',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='devices_ip_addresses',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='dl_workflow',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='fiscal_officer',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='for_coursework',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
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
        migrations.AddField(
            model_name='historicalallocation',
            name='it_pros',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='leverage_multiple_gpus',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='phi_association',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='primary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='secondary_contact',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='storage_space',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='sub_account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='system',
            field=models.CharField(blank=True, choices=[('Carbonate', 'Carbonate'), ('BigRed3', 'Big Red 3')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='training_or_inference',
            field=models.CharField(blank=True, choices=[('Training', 'Training'), ('Inference', 'Inference'), ('Both', 'Both')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='use_indefinitely',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='allocation',
            name='quantity',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalallocation',
            name='quantity',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
