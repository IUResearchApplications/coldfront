# Generated by Django 3.2.13 on 2022-07-21 16:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('allocation', '0004_auto_20211005_1108'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllocationChangeRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('end_date_extension', models.IntegerField(blank=True, null=True)),
                ('justification', models.TextField()),
                ('notes', models.CharField(blank=True, max_length=512, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AllocationChangeStatusChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AllocationUserRequestStatusChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='allocation',
            name='campus_affiliation',
            field=models.CharField(blank=True, choices=[('BL', 'IU Bloomington'), ('IN', 'IUPUI (Indianapolis)'), ('CO', 'IUPUC (Columbus)'), ('EA', 'IU East (Richmond)'), ('FW', 'IU Fort Wayne'), ('CO', 'IU Kokomo'), ('NW', 'IU Northwest (Gary)'), ('SB', 'IU South Bend'), ('SE', 'IU Southeast (New Albany)'), ('OR', 'Other')], max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='data_manager',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='email',
            field=models.EmailField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='faculty_email',
            field=models.EmailField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='first_name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='is_changeable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='allocation',
            name='last_name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='project_directory_name',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='storage_space_unit',
            field=models.CharField(blank=True, choices=[('GB', 'GB'), ('TB', 'TB')], max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='store_ephi',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='total_cost',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='allocation',
            name='url',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='allocationattributetype',
            name='is_changeable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='campus_affiliation',
            field=models.CharField(blank=True, choices=[('BL', 'IU Bloomington'), ('IN', 'IUPUI (Indianapolis)'), ('CO', 'IUPUC (Columbus)'), ('EA', 'IU East (Richmond)'), ('FW', 'IU Fort Wayne'), ('CO', 'IU Kokomo'), ('NW', 'IU Northwest (Gary)'), ('SB', 'IU South Bend'), ('SE', 'IU Southeast (New Albany)'), ('OR', 'Other')], max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='data_manager',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='email',
            field=models.EmailField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='faculty_email',
            field=models.EmailField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='first_name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='is_changeable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='last_name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='project_directory_name',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='storage_space_unit',
            field=models.CharField(blank=True, choices=[('GB', 'GB'), ('TB', 'TB')], max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='store_ephi',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='total_cost',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocation',
            name='url',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalallocationattributetype',
            name='is_changeable',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='allocation',
            name='storage_space',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalallocation',
            name='storage_space',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='HistoricalAllocationUserRequest',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('allocation_user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationuser')),
                ('allocation_user_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationuserstatuschoice')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('requestor_user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationuserrequeststatuschoice')),
            ],
            options={
                'verbose_name': 'historical allocation user request',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalAllocationChangeRequest',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('end_date_extension', models.IntegerField(blank=True, null=True)),
                ('justification', models.TextField()),
                ('notes', models.CharField(blank=True, max_length=512, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('allocation', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocation')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationchangestatuschoice', verbose_name='Status')),
            ],
            options={
                'verbose_name': 'historical allocation change request',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalAllocationAttributeChangeRequest',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('new_value', models.CharField(max_length=128)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('allocation_attribute', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationattribute')),
                ('allocation_change_request', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='allocation.allocationchangerequest')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical allocation attribute change request',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='AllocationUserRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('allocation_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationuser')),
                ('allocation_user_status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationuserstatuschoice')),
                ('requestor_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationuserrequeststatuschoice')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AllocationInvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('account_number', models.CharField(max_length=9)),
                ('sub_account_number', models.CharField(blank=True, max_length=20, null=True)),
                ('allocation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocation')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationstatuschoice')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='allocationchangerequest',
            name='allocation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocation'),
        ),
        migrations.AddField(
            model_name='allocationchangerequest',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationchangestatuschoice', verbose_name='Status'),
        ),
        migrations.CreateModel(
            name='AllocationAttributeChangeRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('new_value', models.CharField(max_length=128)),
                ('allocation_attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationattribute')),
                ('allocation_change_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.allocationchangerequest')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
