from datetime import datetime, timedelta

from django.dispatch import receiver

from coldfront.core.allocation.signals import (allocation_activate_user,
                                               allocation_remove_user,
                                               allocation_change_user_role,
                                               allocation_change,
                                               allocation_expire,
                                               allocation_activate,
                                               visit_allocation_detail)
from coldfront.core.allocation.views import (AllocationAddUsersView,
                                             AllocationChangeView,
                                             AllocationRemoveUsersView,
                                             AllocationUserDetailView,
                                             AllocationDetailView)
from coldfront.core.allocation.tasks import update_statuses
from coldfront.core.allocation.models import AllocationChangeRequest, AllocationUser, Allocation
from coldfront.core.project.views import (ProjectAddUsersView,
                                          ProjectRemoveUsersView,
                                          ProjectArchiveProjectView,
                                          ProjectReviewDenyView)
from coldfront.plugins.slate_project.utils import (add_user_to_slate_project_group,
                                                   add_gid_allocation_attribute,
                                                   remove_user_from_slate_project_group,
                                                   change_users_slate_project_groups,
                                                   update_user_status,
                                                   send_expiry_email,
                                                   sync_slate_project_users,
                                                   sync_slate_project_ldap_group,
                                                   sync_slate_project_user_statuses,
                                                   sync_slate_project_allocated_quantity,
                                                   send_new_allocation_change_request_email,
                                                   send_new_allocation_removal_request_email)
from coldfront.plugins.allocation_removal_requests.views import AllocationRemovalRequestView
from coldfront.plugins.allocation_removal_requests.models import AllocationRemovalRequest
from coldfront.plugins.allocation_removal_requests.signals import allocation_removal_request
from coldfront.plugins.customizable_forms.views import GenericView
from coldfront.core.allocation.signals import allocation_new


@receiver(allocation_change, sender=AllocationChangeView)
def send_allocation_change_request_email(sender, **kwargs):
    allocation_change_pk = kwargs.get('allocation_change_pk')
    allocation_change_obj = AllocationChangeRequest.objects.get(pk=allocation_change_pk)
    if not allocation_change_obj.allocation.get_parent_resource.name == 'Slate Project':
        return

    send_new_allocation_change_request_email(allocation_change_obj)

@receiver(allocation_activate, sender=AllocationDetailView)
def add_group(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    allocation_obj = Allocation.objects.get(pk=allocation_pk)
    if not allocation_obj.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_obj.status.name == 'Active':
        return

    add_gid_allocation_attribute(allocation_obj)
    for allocation_user_obj in allocation_obj.allocationuser_set.filter(status__name='Pending'):
        update_user_status(allocation_user_obj, 'Active')
        add_user_to_slate_project_group(allocation_user_obj)

@receiver(allocation_activate_user, sender=ProjectAddUsersView)
@receiver(allocation_activate_user, sender=AllocationAddUsersView)
def activate_user(sender, **kwargs):
    allocation_user_pk = kwargs.get('allocation_user_pk')
    allocation_user_obj = AllocationUser.objects.get(pk=allocation_user_pk)
    if not allocation_user_obj.allocation.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_user_obj.allocation.status.name in ['Active', 'Renewal Requested']:
        return
    if not allocation_user_obj.status.name in ['Active', 'Invited', 'Disabled', 'Retired']:
        return
    add_user_to_slate_project_group(allocation_user_obj)

@receiver(allocation_new, sender=GenericView)
def update_new_allocation_users(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    allocation_obj = Allocation.objects.get(pk=allocation_pk)
    if not allocation_obj.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_obj.status.name in ['New']:
        return
    for allocation_user_obj in allocation_obj.allocationuser_set.filter(status__name='Active'):
        update_user_status(allocation_user_obj, 'Pending')

@receiver(allocation_activate_user, sender=ProjectAddUsersView)
@receiver(allocation_activate_user, sender=AllocationAddUsersView)
def add_user(sender, **kwargs):
    allocation_user_pk = kwargs.get('allocation_user_pk')
    allocation_user_obj = AllocationUser.objects.get(pk=allocation_user_pk)
    if not allocation_user_obj.allocation.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_user_obj.allocation.status.name in ['New']:
        return
    update_user_status(allocation_user_obj, 'Pending')

@receiver(allocation_remove_user, sender=AllocationRemoveUsersView)
@receiver(allocation_remove_user, sender=ProjectRemoveUsersView)
def remove_user(sender, **kwargs):
    allocation_user_pk = kwargs.get('allocation_user_pk')
    allocation_user_obj = AllocationUser.objects.get(pk=allocation_user_pk)
    if not allocation_user_obj.allocation.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_user_obj.allocation.status.name in ['Active', 'Renewal Requested']:
        return

    remove_user_from_slate_project_group(allocation_user_obj)

@receiver(allocation_change_user_role, sender=AllocationUserDetailView)
def change_user_role(sender, **kwargs):
    allocation_user_pk = kwargs.get('allocation_user_pk')
    allocation_user_obj = AllocationUser.objects.get(pk=allocation_user_pk)
    if not allocation_user_obj.allocation.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_user_obj.allocation.status.name in ['Active', 'Renewal Requested']:
        return
    if not allocation_user_obj.status.name in ['Active', 'Invited', 'Disabled', 'Retired']:
        return

    change_users_slate_project_groups(allocation_user_obj)

@receiver(allocation_expire, sender=update_statuses)
@receiver(allocation_expire, sender=ProjectArchiveProjectView)
@receiver(allocation_expire, sender=ProjectReviewDenyView)
def expire(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    allocation_obj = Allocation.objects.get(pk=allocation_pk)
    if not allocation_obj.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_obj.status.name == 'Expired':
        return

    send_expiry_email(allocation_obj)

@receiver(allocation_removal_request, sender=AllocationRemovalRequestView)
def remove(sender, **kwargs):
    allocation_removal_request_pk = kwargs.get('allocation_removal_request_pk')
    allocation_removal_request_obj = AllocationRemovalRequest.objects.get(pk=allocation_removal_request_pk)
    if not allocation_removal_request_obj.allocation.get_parent_resource.name == 'Slate Project':
        return

    send_new_allocation_removal_request_email(allocation_removal_request_obj)

@receiver(visit_allocation_detail, sender=AllocationDetailView)
def sync_slate_project(sender, **kwargs):
    allocation_pk = kwargs.get('allocation_pk')
    allocation_obj = Allocation.objects.get(pk=allocation_pk)
    if not allocation_obj.get_parent_resource.name == 'Slate Project':
        return
    if not allocation_obj.status.name in ['Active', 'Renewal Requested']:
        return

    sync_slate_project_ldap_group(allocation_obj)
    sync_slate_project_users(allocation_obj)
    sync_slate_project_allocated_quantity(allocation_obj)

    slate_project_user_objs = AllocationUser.objects.filter(
        allocation = allocation_obj,
        status__name__in=['Active', 'Invited', 'Disabled', 'Retired'],
        modified__lt = datetime.now() - timedelta(seconds=5)
    ).select_related('user', 'status', 'allocation', 'allocation__project')
    sync_slate_project_user_statuses(slate_project_user_objs)
