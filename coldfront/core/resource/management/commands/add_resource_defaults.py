from django.core.management.base import BaseCommand

from coldfront.core.resource.models import (AttributeType,
                                            ResourceAttributeType,
                                            ResourceType)


class Command(BaseCommand):
    help = 'Add default resource related choices'

    def handle(self, *args, **options):

        for attribute_type in ('Active/Inactive', 'Date', 'Int', 
            'Public/Private', 'Text', 'Yes/No', 'Attribute Expanded Text', 'True/False'):
            AttributeType.objects.get_or_create(name=attribute_type)

        for resource_attribute_type, attribute_type in (
            ('Core Count', 'Int'),
            ('expiry_time', 'Int'),
            ('fee_applies', 'Yes/No'),
            ('Node Count', 'Int'),
            ('Owner', 'Text'),
            ('quantity_default_value', 'Int'),
            ('quantity_label', 'Text'),
            ('eula', 'Text'),
            ('OnDemand','Yes/No'),
            ('ServiceEnd', 'Date'),
            ('ServiceStart', 'Date'),
            ('slurm_cluster', 'Text'),
            ('slurm_specs', 'Attribute Expanded Text'),
            ('slurm_specs_attriblist', 'Text'),
            ('Status', 'Public/Private'),
            ('Vendor', 'Text'),
            ('Model', 'Text'),
            ('SerialNumber', 'Text'),
            ('RackUnits', 'Int'),
            ('InstallDate', 'Date'),
            ('WarrantyExpirationDate', 'Date'),
            ('access_level', 'Text'),
            ('access_level_label', 'Text'),
            ('account_number', 'Text'),
            ('account_number_label', 'Text'),
            ('applications_list', 'Text'),
            ('applications_list_label', 'Text'),
            ('campus_affiliation', 'Text'),
            ('campus_affiliation_label', 'Text'),
            ('check_user_account', 'Text'),
            ('confirm_understanding', 'True/False'),
            ('confirm_understanding_label', 'Text'),
            ('cost', 'Int'),
            ('cost_label', 'Text'),
            ('data_management_plan', 'Text'),
            ('data_management_plan_label', 'Text'),
            ('data_manager', 'Text'),
            ('data_manager_label', 'Text'),
            ('department_full_name', 'Text'),
            ('department_full_name_label', 'Text'),
            ('department_short_name', 'Text'),
            ('department_short_name_label', 'Text'),
            ('devices_ip_addresses', 'Text'),
            ('devices_ip_addresses_label', 'Text'),
            ('dl_workflow', 'Yes/No'),
            ('dl_workflow_label', 'Text'),
            ('email', 'Text'),
            ('email_label', 'Text'),
            ('end_date', 'Date'),
            ('end_date_label', 'Text'),
            ('expiry_time', 'Int'),
            ('faculty_email', 'Text'),
            ('faculty_email_label', 'Text'),
            ('first_name', 'Text'),
            ('first_name_label', 'Text'),
            ('fiscal_officer', 'Text'),
            ('fiscal_officer_label', 'Text'),
            ('for_coursework', 'Yes/No'),
            ('for_coursework_label', 'Text'),
            ('it_pros', 'Text'),
            ('it_pros_label', 'Text'),
            ('last_name', 'Text'),
            ('last_name_label', 'Text'),
            ('leverage_multiple_gpus', 'Yes/No'),
            ('leverage_multiple_gpus_label', 'Text'),
            ('phi_association', 'Yes/No'),
            ('phi_association_label', 'Text'),
            ('primary_contact', 'Text'),
            ('primary_contact_label', 'Text'),
            ('project_directory_name', 'Text'),
            ('project_directory_name_label', 'Text'),
            ('prorated', 'True/False'),
            ('prorated_cost_label', 'Text'),
            ('requires_user_request', 'Yes/No'),
            ('secondary_contact', 'Text'),
            ('secondary_contact_label', 'Text'),
            ('start_date', 'Date'),
            ('start_date_label', 'Text'),
            ('storage_space', 'Int'),
            ('storage_space_label', 'Text'),
            ('storage_space_unit', 'Text'),
            ('storage_space_unit_label', 'Text'),
            ('store_ephi', 'Yes/No'),
            ('store_ephi_label', 'Text'),
            ('sub_account_number', 'Text'),
            ('sub_account_number_label', 'Text'),
            ('system', 'Text'),
            ('system_label', 'Text'),
            ('training_or_inference', 'Text'),
            ('training_or_inference_label', 'Text'),
            ('url', 'Text'),
            ('url_label', 'Text'),
            ('user_limit', 'Int')
        ):
            ResourceAttributeType.objects.get_or_create(
                name=resource_attribute_type, attribute_type=AttributeType.objects.get(name=attribute_type))

        for resource_type, description in (
            ('Cloud', 'Cloud Computing'),
            ('Cluster', 'Cluster servers'),
            ('Cluster Partition', 'Cluster Partition '),
            ('Compute Node', 'Compute Node'),
            ('Server', 'Extra servers providing various services'),
            ('Software License', 'Software license purchased by users'),
            ('Storage', 'NAS storage'),
        ):
            ResourceType.objects.get_or_create(
                name=resource_type, description=description)
