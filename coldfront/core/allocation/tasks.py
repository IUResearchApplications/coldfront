import datetime
# import the logging library
import logging

from coldfront.core.allocation.models import (Allocation,
                                              AllocationStatusChoice)
from coldfront.core.user.models import User
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import send_email_template
from coldfront.core.allocation.signals import allocation_expire

# Get an instance of a logger
logger = logging.getLogger(__name__)


CENTER_NAME = import_from_settings('CENTER_NAME')
CENTER_BASE_URL = import_from_settings('CENTER_BASE_URL')
CENTER_PROJECT_RENEWAL_HELP_URL = import_from_settings(
    'CENTER_PROJECT_RENEWAL_HELP_URL')
EMAIL_SENDER = import_from_settings('EMAIL_SENDER')
EMAIL_OPT_OUT_INSTRUCTION_URL = import_from_settings(
    'EMAIL_OPT_OUT_INSTRUCTION_URL')
EMAIL_SIGNATURE = import_from_settings('EMAIL_SIGNATURE')
EMAIL_ALLOCATION_EXPIRING_NOTIFICATION_DAYS = import_from_settings(
    'EMAIL_ALLOCATION_EXPIRING_NOTIFICATION_DAYS', [7, ])

EMAIL_ADMINS_ON_ALLOCATION_EXPIRE = import_from_settings('EMAIL_ADMINS_ON_ALLOCATION_EXPIRE')
EMAIL_ADMIN_LIST = import_from_settings('EMAIL_ADMIN_LIST')

EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings('EMAIL_TICKET_SYSTEM_ADDRESS')


def update_statuses():

    expired_status_choice = AllocationStatusChoice.objects.get(
        name='Expired')
    allocations_to_expire = Allocation.objects.filter(
        status__name__in=['Active', 'Payment Pending', 'Payment Requested', 'Unpaid', ],
        end_date__lt=datetime.datetime.now().date(),
        project__requires_review=True
    )
    for sub_obj in allocations_to_expire:
        sub_obj.status = expired_status_choice
        sub_obj.save()

        allocation_expire.send(sender=update_statuses, allocation_pk=sub_obj.pk)

    logger.info(f'Allocations set to expired: {allocations_to_expire.count()}')


def send_expiry_emails():
    #Allocations expiring soon
    for user in User.objects.all():
        projectdict = {}
        expirationdict = {}
        email_receiver_list = []
        for days_remaining in sorted(set(EMAIL_ALLOCATION_EXPIRING_NOTIFICATION_DAYS)):

            expring_in_days = (datetime.datetime.today(
                ) + datetime.timedelta(days=days_remaining)).date()
                       
            for allocationuser in user.allocationuser_set.all():
                allocation = allocationuser.allocation

                if (((allocation.status.name in ['Active', 'Payment Pending', 'Payment Requested', 'Unpaid']) and (allocation.end_date == expring_in_days))):
                    if not allocation.project.requires_review:
                        continue

                    project_url = f'{CENTER_BASE_URL.strip("/")}/{"project"}/{allocation.project.pk}/'

                    allocation_renew_url = f'{CENTER_BASE_URL.strip("/")}/{"allocation"}/{allocation.pk}/'

                    resource_name = allocation.get_parent_resource.name

                    template_context = {
                        'center_name': CENTER_NAME,
                        'expring_in_days': days_remaining,
                        'project_dict': projectdict,
                        'expiration_dict': expirationdict,
                        'expiration_days': sorted(set(EMAIL_ALLOCATION_EXPIRING_NOTIFICATION_DAYS)),
                        'project_renewal_help_url': CENTER_PROJECT_RENEWAL_HELP_URL,
                        'opt_out_instruction_url': EMAIL_OPT_OUT_INSTRUCTION_URL,
                        'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                        'signature': EMAIL_SIGNATURE
                    }
                    
                    expire_notification = allocation.allocationattribute_set.filter(
                        allocation_attribute_type__name='EXPIRE NOTIFICATION').first()
                    if expire_notification and expire_notification.value == 'No':
                        continue

                    cloud_usage_notification = allocation.allocationattribute_set.filter(
                        allocation_attribute_type__name='CLOUD_USAGE_NOTIFICATION').first()
                    if cloud_usage_notification and cloud_usage_notification.value == 'No':
                        continue

                    for projectuser in allocation.project.projectuser_set.filter(user=user, status__name='Active'): 
                        if ((projectuser.enable_notifications) and 
                            (allocationuser.user == user and allocationuser.status.name == 'Active')):

                            if (user.email not in email_receiver_list):
                                email_receiver_list.append(user.email)

                            if days_remaining not in expirationdict:
                                expirationdict[days_remaining] = []
                                expirationdict[days_remaining].append((project_url, allocation_renew_url, resource_name))
                            else:
                                expirationdict[days_remaining].append((project_url, allocation_renew_url, resource_name))

                            if allocation.project.title not in projectdict:
                                projectdict[allocation.project.title] = (
                                    project_url,
                                    allocation.project.pi.username,
                                    allocation.project.get_env.get('renewable'),
                                    allocation.project.type.name
                                    )
                            
        if email_receiver_list:
            send_email_template(f'Your access to {CENTER_NAME}\'s resources is expiring soon',
                        'email/allocation_expiring.txt',
                        template_context,
                        EMAIL_TICKET_SYSTEM_ADDRESS,
                        email_receiver_list
                        ) 

            logger.debug(f'Allocation(s) expiring in soon, email sent to user {user}.')

    #Allocations expired
    admin_projectdict = {}
    admin_allocationdict = {}
    for user in User.objects.all():
        projectdict = {}
        allocationdict = {}
        email_receiver_list = []
        
        expring_in_days = (datetime.datetime.today() + datetime.timedelta(days=-1)).date()
                
        for allocationuser in user.allocationuser_set.all():
            allocation = allocationuser.allocation

            if allocation.status.name != 'Active':
                continue

            if not allocation.project.requires_review:
                continue

            if (allocation.end_date == expring_in_days and not allocation.is_locked):
                
                project_url = f'{CENTER_BASE_URL.strip("/")}/{"project"}/{allocation.project.pk}/'

                allocation_renew_url = f'{CENTER_BASE_URL.strip("/")}/{"allocation"}/{allocation.pk}/'

                allocation_url = f'{CENTER_BASE_URL.strip("/")}/{"allocation"}/{allocation.pk}/'

                resource_name = allocation.get_parent_resource.name

                template_context = {
                    'center_name': CENTER_NAME,
                    'project_dict': projectdict,
                    'allocation_dict': allocationdict,
                    'project_renewal_help_url': CENTER_PROJECT_RENEWAL_HELP_URL,
                    'opt_out_instruction_url': EMAIL_OPT_OUT_INSTRUCTION_URL,
                    'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                    'signature': EMAIL_SIGNATURE
                }

                expire_notification = allocation.allocationattribute_set.filter(
                    allocation_attribute_type__name='EXPIRE NOTIFICATION').first()

                for projectuser in allocation.project.projectuser_set.filter(user=user, status__name='Active'): 
                    if ((projectuser.enable_notifications) and 
                        (allocationuser.user == user and allocationuser.status.name == 'Active')):

                        if not expire_notification or expire_notification and expire_notification.value == 'No':

                            if (user.email not in email_receiver_list):
                                email_receiver_list.append(user.email)

                            if project_url not in allocationdict:
                                    allocationdict[project_url] = []
                                    allocationdict[project_url].append({allocation_renew_url : resource_name})
                            else:
                                if {allocation_renew_url : resource_name} not in allocationdict[project_url]:
                                    allocationdict[project_url].append({allocation_renew_url : resource_name})

                            if allocation.project.title not in projectdict:
                                projectdict[allocation.project.title] = (
                                    project_url,
                                    allocation.project.pi.username,
                                    allocation.project.get_env.get('renewable'),
                                    allocation.project.type.name
                                    )

                        if EMAIL_ADMINS_ON_ALLOCATION_EXPIRE:
                            
                            if project_url not in admin_allocationdict:
                                    admin_allocationdict[project_url] = []
                                    admin_allocationdict[project_url].append({allocation_url : resource_name})
                            else:
                                if {allocation_url : resource_name} not in admin_allocationdict[project_url]:
                                    admin_allocationdict[project_url].append({allocation_url : resource_name})

                            if allocation.project.title not in admin_projectdict:
                                admin_projectdict[allocation.project.title] = (project_url, allocation.project.pi.username)

                            
        if email_receiver_list:

            send_email_template('Your access to resource(s) have expired',
                        'email/allocation_expired.txt',
                        template_context,
                        EMAIL_TICKET_SYSTEM_ADDRESS,
                        email_receiver_list
                        ) 

            logger.debug(f'Allocation(s) expired email sent to user {user}.')

    if EMAIL_ADMINS_ON_ALLOCATION_EXPIRE:

        if admin_projectdict:

            admin_template_context = {
                'project_dict': admin_projectdict,
                'allocation_dict': admin_allocationdict,
                'signature': EMAIL_SIGNATURE
            }  
            
            send_email_template('Allocation(s) have expired',
                                'email/admin_allocation_expired.txt',
                                admin_template_context,
                                EMAIL_SENDER,
                                [EMAIL_ADMIN_LIST,]
                                )
