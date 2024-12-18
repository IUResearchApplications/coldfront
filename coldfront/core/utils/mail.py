import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from coldfront.core.utils.common import import_from_settings

logger = logging.getLogger(__name__)
EMAIL_ENABLED = import_from_settings('EMAIL_ENABLED', False)
EMAIL_SUBJECT_PREFIX = import_from_settings('EMAIL_SUBJECT_PREFIX')
EMAIL_DEVELOPMENT_EMAIL_LIST = import_from_settings('EMAIL_DEVELOPMENT_EMAIL_LIST')
EMAIL_SENDER = import_from_settings('EMAIL_SENDER')
EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings('EMAIL_TICKET_SYSTEM_ADDRESS')
EMAIL_OPT_OUT_INSTRUCTION_URL = import_from_settings('EMAIL_OPT_OUT_INSTRUCTION_URL')
EMAIL_SIGNATURE = import_from_settings('EMAIL_SIGNATURE')
EMAIL_CENTER_NAME = import_from_settings('CENTER_NAME')
CENTER_BASE_URL = import_from_settings('CENTER_BASE_URL')
EMAIL_GROUP_TO_EMAIL_MAPPING = import_from_settings('EMAIL_GROUP_TO_EMAIL_MAPPING', {})


def send_email(subject, body, sender, receiver_list, cc=[]):
    """Helper function for sending emails
    """

    if not EMAIL_ENABLED:
        return

    if len(receiver_list) == 0:
        logger.error(f'Failed to send email with subject {subject}, missing receiver_list')
        return

    if len(sender) == 0:
        logger.error(f'Failed to send email with subject {subject}, missing sender address')
        return

    if len(EMAIL_SUBJECT_PREFIX) > 0:
        subject = EMAIL_SUBJECT_PREFIX + ' ' + subject

    if settings.DEBUG:
        receiver_list = EMAIL_DEVELOPMENT_EMAIL_LIST

    if cc and settings.DEBUG:
        cc = EMAIL_DEVELOPMENT_EMAIL_LIST

    try:
        if cc:
            email = EmailMessage(
                subject,
                body,
                sender,
                receiver_list,
                cc=cc)
            email.send(fail_silently=False)
        else:
            send_mail(subject, body, sender,
                      receiver_list, fail_silently=False)
    except SMTPException as e:
        logger.error('Failed to send email to %s from %s with subject %s',
                     sender, ','.join(receiver_list), subject)


def send_email_template(subject, template_name, template_context, sender, receiver_list):
    """Helper function for sending emails from a template
    """
    if not EMAIL_ENABLED:
        return

    body = render_to_string(template_name, template_context)

    return send_email(subject, body, sender, receiver_list)

def email_template_context():
    """Basic email template context used as base for all templates
    """
    return {
        'center_name': EMAIL_CENTER_NAME,
        'signature': EMAIL_SIGNATURE,
        'opt_out_instruction_url': EMAIL_OPT_OUT_INSTRUCTION_URL
    }

def build_link(url_path, domain_url=''):
    if not domain_url:
        domain_url = CENTER_BASE_URL
    return f'{domain_url}{url_path}'

def send_admin_email_template(allocation_obj, subject, template_name, template_context):
    """Helper function for sending admin emails using a template
    """
    email_recipient = get_email_recipient_from_groups(
        allocation_obj.get_parent_resource.review_groups.all()
    )
    send_email_template(subject, template_name, template_context, EMAIL_SENDER, [email_recipient, ])

def send_allocation_admin_email(allocation_obj, subject, template_name, url_path='', domain_url='', addtl_context = None):
    """Send allocation admin emails
    """
    if not url_path:
        url_path = reverse('allocation-request-list')

    url = build_link(url_path, domain_url=domain_url)
    pi_name = f'{allocation_obj.project.pi.first_name} {allocation_obj.project.pi.last_name} ({allocation_obj.project.pi.username})'
    resource_name = allocation_obj.get_parent_resource

    ctx = email_template_context()
    ctx['pi'] = pi_name
    ctx['resource'] = resource_name
    ctx['url'] = url

    if addtl_context:
        ctx.update(addtl_context)

    send_admin_email_template(
        allocation_obj,
        f'{subject}: {pi_name} - {resource_name}',
        template_name,
        ctx,
    )

def send_allocation_customer_email(allocation_obj, subject, template_name, url_path='', domain_url='', addtl_context=None):
    """Send allocation customer emails
    """
    if not url_path:
        url_path = reverse('allocation-detail', kwargs={'pk': allocation_obj.pk})

    url = build_link(url_path, domain_url=domain_url)
    ctx = email_template_context()
    ctx['resource'] = allocation_obj.get_parent_resource
    ctx['url'] = url

    if addtl_context:
        ctx.update(addtl_context)

    allocation_users = allocation_obj.allocationuser_set.exclude(status__name__in=['Removed', 'Error'])
    email_receiver_list = []
    for allocation_user in allocation_users:
        if allocation_user.allocation.project.projectuser_set.get(
                                user=allocation_user.user).enable_notifications:
            email_receiver_list.append(allocation_user.user.email)

    send_email_template(
        subject,
        template_name,
        ctx,
        EMAIL_SENDER,
        email_receiver_list
    )

def get_email_recipient_from_groups(groups):
    """
    Returns a group's email if it exists in EMAIL_GROUP_TO_EMAIL_MAPPING. Only returns the first
    email it finds, if no email is found then EMAIL_TICKET_SYSTEM_ADDRESS is returned.

    :params groups: List/QuerySet of Groups
    :return: Email address for a group if found, else EMAIL_TICKET_SYSTEM_ADDRESS
    """
    for group in groups:
        email = EMAIL_GROUP_TO_EMAIL_MAPPING.get(group.name)
        if email is not None:
            return email

    return EMAIL_TICKET_SYSTEM_ADDRESS
