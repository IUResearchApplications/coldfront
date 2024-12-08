import logging
from django.urls import reverse
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.core.utils.mail import build_link
from coldfront.plugins.slate_project import utils
from coldfront.plugins.slate_project.forms import SlateProjectSearchForm
from coldfront.core.project.models import Project
from coldfront.core.utils.common import get_domain_url, import_from_settings
from coldfront.core.utils.mail import send_email_template

EMAIL_ENABLED = import_from_settings('EMAIL_ENABLED', False)
if EMAIL_ENABLED:
    SLATE_PROJECT_EMAIL = import_from_settings('SLATE_PROJECT_EMAIL', '')
    EMAIL_SIGNATURE = import_from_settings('EMAIL_SIGNATURE')
    EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings('EMAIL_TICKET_SYSTEM_ADDRESS')
    EMAIL_CENTER_NAME = import_from_settings('CENTER_NAME')

logger = logging.getLogger(__name__)


@login_required
def get_slate_project_info(request):
    slate_projects = utils.get_slate_project_info(request.POST.get('viewed_username'))

    context = {
        'slate_projects': slate_projects
    }

    return render(request, 'slate_project/slate_project_info.html', context)

def get_slate_project_estimated_cost(request):
    allocation_obj = Allocation.objects.get(pk=request.POST.get('allocation_pk'))

    estimated_cost = utils.get_estimated_storage_cost(allocation_obj)
    context = {'estimated_cost': estimated_cost}

    return render(request, 'slate_project/estimated_cost.html', context)

def slate_project_search_view(request):
    context = {'form': SlateProjectSearchForm()}
    return render(request, 'slate_project/slate_project_search.html', context)


class SlateProjectSearchResultsView(LoginRequiredMixin, ListView):
    template_name = 'slate_project/slate_project_search_results.html'

    def post(self, request, *args, **kwargs):
        slate_project = request.POST.get('slate_project')
        context = {}
        # icontains does not work with our database implementation
        slate_project_objs = AllocationAttribute.objects.filter(
            allocation_attribute_type__name='Slate Project Directory',
            allocation__resources__name='Slate Project',
            allocation__status__name='Active',
            allocation__project__status__name='Active',
            # value__icontains='/N/project/' + slate_project
        )
        slate_projects = []
        for slate_project_obj in slate_project_objs:
            if not slate_project.lower() in slate_project_obj.value.lower():
                continue
            allocation_users = slate_project_obj.allocation.allocationuser_set.filter(
                status__name__in=['Active', 'Eligible']).values_list('user', flat=True)

            slate_project = slate_project_obj.value.split('/')[-1]
            slate_projects.append(
                {
                    'slate_project': slate_project_obj,
                    'slate_project_name': slate_project,
                    'allocation_users': allocation_users,
                    'pi': slate_project_obj.allocation.project.pi,
                }
            )

        context['slate_projects'] = slate_projects
        context['EMAIL_ENABLED'] = EMAIL_ENABLED
        return render(request, self.template_name, context)


class RequestAccessEmailView(LoginRequiredMixin, View):

    def post(self, request):
        allocation_obj = get_object_or_404(Allocation, pk=request.POST.get('allocation_pk'))
        project_obj = allocation_obj.project
        if allocation_obj.project.private is True:
            logger.warning(
                f'User {request.user.username} attempted to request access to a slate project '
                f'allocation (allocation pk={allocation_obj.pk}) in a private project'
            )
            return HttpResponseForbidden(reverse('project-list'))

        allocation_url = build_link(reverse('allocation-detail', kwargs={'pk': allocation_obj.pk}))
        project_url = build_link(reverse('project-detail', kwargs={'pk': project_obj.pk}))

        if EMAIL_ENABLED:
            send_email_template(
                'Add User to Slate Project Request',
                'slate_project/email/slate_project_add_user_request.txt',
                {
                    'center_name': EMAIL_CENTER_NAME,
                    'user': request.user,
                    'project_title': project_obj.title,
                    'project_url': project_url,
                    'slate_project_url': allocation_url,
                    'help_email': SLATE_PROJECT_EMAIL,
                    'signature': EMAIL_SIGNATURE
                },
                EMAIL_TICKET_SYSTEM_ADDRESS,
                [project_obj.pi.email]
            )
            logger.info(
                f'User {request.user.username} sent an email to {project_obj.pi.email} requesting '
                f'access to their slate project allocation (allocation pk={allocation_obj.pk})'
            )
        else:
            logger.warning('Email has not been enabled')
            return HttpResponseForbidden(reverse('project-list'))

        return HttpResponseRedirect(reverse('project-list'))