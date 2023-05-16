import datetime
import urllib
import logging
import csv

from django.conf import settings
from django.contrib import messages
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.utils.html import format_html
from django.http.response import StreamingHttpResponse

from coldfront.core.allocation.models import (Allocation,
                                              AllocationStatusChoice,
                                              AllocationUser,
                                              AllocationUserStatusChoice)
from coldfront.core.allocation.signals import (allocation_activate_user,
                                               allocation_remove_user)
from coldfront.core.grant.models import Grant
from coldfront.core.project.forms import (ProjectAddUserForm,
                                          ProjectUpdateForm,
                                          ProjectAddUsersToAllocationForm,
                                          ProjectFormSetWithSelectDisabled,
                                          ProjectRemoveUserForm,
                                          ProjectRemoveUserFormset,
                                          ProjectReviewEmailForm,
                                          ProjectRequestEmailForm,
                                          ProjectReviewForm, ProjectSearchForm,
                                          ProjectPISearchForm,
                                          ProjectUserUpdateForm,
                                          ProjectReviewAllocationForm,
                                          ProjectUserExportForm,
                                          ProjectExportForm,)
from coldfront.core.project.models import (Project, ProjectReview,
                                           ProjectReviewStatusChoice,
                                           ProjectStatusChoice, ProjectUser,
                                           ProjectUserRoleChoice,
                                           ProjectUserStatusChoice,
                                           ProjectUserMessage,
                                           ProjectDescriptionRecord)
from coldfront.core.publication.models import Publication
from coldfront.core.research_output.models import ResearchOutput
from coldfront.core.user.forms import UserSearchForm
from coldfront.core.user.utils import CombinedUserSearch
from coldfront.core.user.models import UserProfile
from coldfront.core.utils.common import Echo
from coldfront.core.utils.common import get_domain_url, import_from_settings
from coldfront.core.utils.mail import send_email, send_email_template
from coldfront.core.project.utils import (get_new_end_date_from_list,
                                          create_admin_action,
                                          get_project_user_emails)
from coldfront.core.allocation.utils import send_added_user_email
from coldfront.core.utils.slack import send_message

logger = logging.getLogger(__name__)

EMAIL_ENABLED = import_from_settings('EMAIL_ENABLED', False)
ALLOCATION_ENABLE_ALLOCATION_RENEWAL = import_from_settings(
    'ALLOCATION_ENABLE_ALLOCATION_RENEWAL', True)
ALLOCATION_DEFAULT_ALLOCATION_LENGTH = import_from_settings(
    'ALLOCATION_DEFAULT_ALLOCATION_LENGTH', 365)
PROJECT_DEFAULT_PROJECT_LENGTH = import_from_settings(
    'PROJECT_DEFAULT_PROJECT_LENGTH', 365
)
ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING = import_from_settings(
    'ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING',
    30
)
ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING = import_from_settings(
    'ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING',
    60
)
PROJECT_CLASS_PROJECT_END_DATES = import_from_settings(
    'PROJECT_CLASS_PROJECT_END_DATES', [(1, 19), (5, 11), (8, 23)]
)
PROJECT_DEFAULT_MAX_MANAGERS = import_from_settings(
    'PROJECT_DEFAULT_MAX_MANAGERS', 3
)
PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING = import_from_settings(
    'PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING', 60
)
PROJECT_END_DATE_CARRYOVER_DAYS = import_from_settings(
    'PROJECT_END_DATE_CARRYOVER_DAYS',  90
)
PROJECT_DAYS_TO_REVIEW_BEFORE_EXPIRING = import_from_settings(
    'PROJECT_DAYS_TO_REVIEW_BEFORE_EXPIRING', 30
)
PROJECT_TYPE_LIMIT_MAPPING = import_from_settings(
    'PROJECT_TYPE_LIMIT_MAPPING', {}
)
SLACK_MESSAGING_ENABLED = import_from_settings(
    'SLACK_MESSAGING_ENABLED', False
)

if EMAIL_ENABLED:
    EMAIL_DIRECTOR_EMAIL_ADDRESS = import_from_settings(
        'EMAIL_DIRECTOR_EMAIL_ADDRESS')
    EMAIL_SENDER = import_from_settings('EMAIL_SENDER')
    EMAIL_SIGNATURE = import_from_settings('EMAIL_SIGNATURE')
    EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings('EMAIL_TICKET_SYSTEM_ADDRESS')
    EMAIL_CENTER_NAME = import_from_settings('CENTER_NAME')
    EMAIL_OPT_OUT_INSTRUCTION_URL = import_from_settings(
        'EMAIL_OPT_OUT_INSTRUCTION_URL')
    EMAIL_ALERTS_EMAIL_ADDRESS = import_from_settings('EMAIL_ALERTS_EMAIL_ADDRESS')


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'project/project_detail.html'
    context_object_name = 'project'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_view_all_projects'):
            return True

        project_obj = self.get_object()

        if project_obj.projectuser_set.filter(user=self.request.user, status__name='Active').exists():
            return True

        messages.error(
            self.request, 'You do not have permission to view the previous page.')
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allocation_submitted = self.request.GET.get('allocation_submitted')
        after_project_creation_get = self.request.GET.get('after_project_creation')
        context['display_modal'] = 'false'
        if allocation_submitted == 'true':
            context['display_modal'] = 'true'

        context['display_project_created_modal'] = 'false'
        if after_project_creation_get == 'true':
            context['display_project_created_modal'] = 'true'

        is_manager = False
        # Can the user update the project?
        if self.request.user.is_superuser:
            context['is_allowed_to_update_project'] = True
        elif self.object.projectuser_set.filter(user=self.request.user).exists():
            project_user = self.object.projectuser_set.get(
                user=self.request.user)
            if project_user.role.name == 'Manager':
                is_manager = True
                context['is_allowed_to_update_project'] = True
            else:
                context['is_allowed_to_update_project'] = False
        else:
            context['is_allowed_to_update_project'] = False

        # Only show 'Active Users'
        project_users = self.object.projectuser_set.filter(
            status__name='Active').order_by('user__username')

        context['mailto'] = 'mailto:' + \
            ','.join([user.user.email for user in project_users])

        if self.request.user.is_superuser or is_manager or self.request.user.has_perm('allocation.can_view_all_allocations'):
            free_allocations = Allocation.objects.prefetch_related(
                'resources'
            ).filter(
                project=self.object,
                resources__requires_payment=False
            ).order_by('-end_date')

            paid_allocations = Allocation.objects.prefetch_related(
                'resources'
            ).filter(
                project=self.object,
                resources__requires_payment=True
            )
        else:
            if self.object.status.name in ['Active', 'New', 'Waiting For Admin Approval', ]:
                free_allocations = Allocation.objects.filter(
                    Q(project=self.object) &
                    Q(project__projectuser__user=self.request.user) &
                    Q(project__projectuser__status__name__in=['Active', ]) &
                    Q(resources__requires_payment=False) &
                    Q(allocationuser__user=self.request.user) &
                    Q(allocationuser__status__name__in=['Active', ])
                ).distinct().order_by('-end_date')

                paid_allocations = Allocation.objects.filter(
                    Q(project=self.object) &
                    Q(project__projectuser__user=self.request.user) &
                    Q(project__projectuser__status__name__in=['Active', ]) &
                    Q(resources__requires_payment=True) &
                    Q(allocationuser__user=self.request.user) &
                    Q(allocationuser__status__name__in=['Active', ])
                ).distinct().order_by('-end_date')
            else:
                free_allocations = Allocation.objects.prefetch_related(
                    'resources'
                ).filter(
                    project=self.object,
                    resources__requires_payment=False
                )

                paid_allocations = Allocation.objects.prefetch_related(
                    'resources'
                ).filter(
                    project=self.object,
                    resources__requires_payment=True
                )

        context['publications'] = Publication.objects.filter(
            project=self.object, status='Active').order_by('-year')
        context['research_outputs'] = ResearchOutput.objects.filter(
            project=self.object).order_by('-created')
        context['grants'] = Grant.objects.filter(
            project=self.object, status__name__in=['Active', 'Pending', 'Archived'])
        context['free_allocations'] = free_allocations
        context['paid_allocations'] = paid_allocations
        context['project_users'] = project_users
        context['ALLOCATION_ENABLE_ALLOCATION_RENEWAL'] = ALLOCATION_ENABLE_ALLOCATION_RENEWAL
        context['PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING'] = PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING
        context['ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING'] = ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING
        context['ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING'] = ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING

        try:
            context['ondemand_url'] = settings.ONDEMAND_URL
        except AttributeError:
            pass

        return context


class ProjectListView(LoginRequiredMixin, ListView):

    model = Project
    template_name = 'project/project_list.html'
    prefetch_related = ['pi', 'status', 'field_of_science', ]
    context_object_name = 'project_list'
    paginate_by = 25

    def get_queryset(self):

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            if direction == 'asc':
                direction = ''
            else:
                direction = '-'
            order_by = direction + order_by
        else:
            order_by = 'id'

        project_search_form = ProjectSearchForm(self.request.GET)

        if project_search_form.is_valid():
            data = project_search_form.cleaned_data
            if data.get('show_all_projects') and (self.request.user.is_superuser or self.request.user.has_perm('project.can_view_all_projects')):
                projects = Project.objects.prefetch_related(
                    'pi',
                    'field_of_science',
                    'status',
                ).filter(
                    status__name__in=[
                        'New',
                        'Active',
                        'Waiting For Admin Approval',
                        'Review Pending',
                        'Expired',
                    ]
                ).order_by(order_by)
            else:
                projects = Project.objects.prefetch_related(
                    'pi',
                    'field_of_science',
                    'status',
                ).filter(
                    Q(
                        status__name__in=[
                            'New',
                            'Active',
                            'Waiting For Admin Approval',
                            'Review Pending',
                            'Expired',
                        ]
                    ) &
                    Q(projectuser__user=self.request.user) &
                    Q(projectuser__status__name='Active')
                ).order_by(order_by)

            # Last Name
            if data.get('last_name'):
                projects = projects.filter(
                    pi__last_name__icontains=data.get('last_name'))

            # Username
            if data.get('username'):
                projects = projects.filter(
                    Q(pi__username__icontains=data.get('username')) |
                    Q(projectuser__user__username__icontains=data.get('username')) &
                    Q(projectuser__status__name='Active')
                )

            # Field of Science
            # if data.get('field_of_science'):
            #     projects = projects.filter(
            #         field_of_science__description__icontains=data.get('field_of_science'))

        else:
            projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                Q(
                    status__name__in=[
                        'New',
                        'Active',
                        'Waiting For Admin Approval',
                        'Review Pending',
                        'Expired',
                    ]
                ) &
                Q(projectuser__user=self.request.user) &
                Q(projectuser__status__name='Active')
            ).order_by(order_by)

        return projects.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects_count = self.get_queryset().count()
        context['projects_count'] = projects_count

        max_projects = self.request.user.userprofile.max_projects
        project_count = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
            Q(pi__username=self.request.user.username) &
            Q(projectuser__status__name='Active') &
            Q(status__name__in=['New', 'Active', 'Review Pending', 'Waiting For Admin Approval', ])
        ).distinct().count()
        # Not being used.
        context['project_requests_remaining'] = 10  # max(0, max_projects - project_count)

        project_pi_search_form = ProjectPISearchForm()
        context['project_pi_search_form'] = project_pi_search_form

        project_search_form = ProjectSearchForm(self.request.GET)
        if project_search_form.is_valid():
            context['project_search_form'] = project_search_form
            data = project_search_form.cleaned_data
            filter_parameters = ''
            for key, value in data.items():
                if value:
                    if isinstance(value, list):
                        for ele in value:
                            filter_parameters += '{}={}&'.format(key, ele)
                    else:
                        filter_parameters += '{}={}&'.format(key, value)
            context['project_search_form'] = project_search_form
        else:
            filter_parameters = None
            context['project_search_form'] = ProjectSearchForm()

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            filter_parameters_with_order_by = filter_parameters + \
                'order_by=%s&direction=%s&' % (order_by, direction)
        else:
            filter_parameters_with_order_by = filter_parameters

        if filter_parameters:
            context['expand_accordion'] = 'show'

        context['filter_parameters'] = filter_parameters
        context['filter_parameters_with_order_by'] = filter_parameters_with_order_by
        context['PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING'] = PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING

        context['project_user_export_form'] = ProjectUserExportForm()
        context['project_export_form'] = ProjectExportForm()
        context['show_export_button'] = self.request.user.is_superuser or self.request.user.has_perm('project.can_view_all_projects')

        project_list = context.get('project_list')
        paginator = Paginator(project_list, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            project_list = paginator.page(page)
        except PageNotAnInteger:
            project_list = paginator.page(1)
        except EmptyPage:
            project_list = paginator.page(paginator.num_pages)

        return context


class ProjectPISearchView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'project/project_pi_list.html'

    def post(self, request, *args, **kwargs):
        pi_username = request.POST.get('pi_username')
        context = {}
        context["pi_username"] = pi_username
        projects = Project.objects.prefetch_related('pi', 'status',).filter(
            pi__username=pi_username,
            projectuser__status__name='Active',
            status__name__in=['New', 'Active', ],
            private=False
        ).distinct()

        new_project_list = []
        for project in projects:
            project_user = project.projectuser_set.filter(user=request.user)
            if project_user.exists():
                if project_user[0].status.name == 'Removed':
                    new_project_list.append(project)
            else:
                new_project_list.append(project)

        context["pi_projects"] = new_project_list
        context['EMAIL_ENABLED'] = EMAIL_ENABLED
        return render(request, self.template_name, context)


class ProjectArchivedListView(LoginRequiredMixin, ListView):

    model = Project
    template_name = 'project/project_archived_list.html'
    prefetch_related = ['pi', 'status', 'field_of_science', ]
    context_object_name = 'project_list'
    paginate_by = 10

    def get_queryset(self):

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            if direction == 'asc':
                direction = ''
            else:
                direction = '-'
            order_by = direction + order_by
        else:
            order_by = 'id'

        project_search_form = ProjectSearchForm(self.request.GET)

        if project_search_form.is_valid():
            data = project_search_form.cleaned_data
            if data.get('show_all_projects') and (self.request.user.is_superuser or self.request.user.has_perm('project.can_view_all_projects')):
                projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                    status__name__in=['Archived', ]).order_by(order_by)
            else:

                projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                    Q(status__name__in=['Archived', ]) &
                    Q(projectuser__user=self.request.user) &
                    Q(projectuser__status__name='Active')
                ).order_by(order_by)

            # Last Name
            if data.get('last_name'):
                projects = projects.filter(
                    pi__last_name__icontains=data.get('last_name'))

            # Username
            if data.get('username'):
                projects = projects.filter(
                    pi__username__icontains=data.get('username'))

            # Field of Science
            # if data.get('field_of_science'):
            #     projects = projects.filter(
            #         field_of_science__description__icontains=data.get('field_of_science'))

        else:
            projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                Q(status__name__in=['Archived', ]) &
                Q(projectuser__user=self.request.user) &
                Q(projectuser__status__name='Active')
            ).order_by(order_by)

        return projects

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        projects_count = self.get_queryset().count()
        context['projects_count'] = projects_count
        context['expand'] = False

        project_search_form = ProjectSearchForm(self.request.GET)
        if project_search_form.is_valid():
            context['project_search_form'] = project_search_form
            data = project_search_form.cleaned_data
            filter_parameters = ''
            for key, value in data.items():
                if value:
                    if isinstance(value, list):
                        for ele in value:
                            filter_parameters += '{}={}&'.format(key, ele)
                    else:
                        filter_parameters += '{}={}&'.format(key, value)
            context['project_search_form'] = project_search_form
        else:
            filter_parameters = None
            context['project_search_form'] = ProjectSearchForm()

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            filter_parameters_with_order_by = filter_parameters + \
                'order_by=%s&direction=%s&' % (order_by, direction)
        else:
            filter_parameters_with_order_by = filter_parameters

        if filter_parameters:
            context['expand_accordion'] = 'show'

        context['filter_parameters'] = filter_parameters
        context['filter_parameters_with_order_by'] = filter_parameters_with_order_by

        project_list = context.get('project_list')
        paginator = Paginator(project_list, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            project_list = paginator.page(page)
        except PageNotAnInteger:
            project_list = paginator.page(1)
        except EmptyPage:
            project_list = paginator.page(paginator.num_pages)

        return context


class ProjectDeniedListView(LoginRequiredMixin, ListView):

    model = Project
    template_name = 'project/project_denied_list.html'
    prefetch_related = ['pi', 'status', 'field_of_science', ]
    context_object_name = 'project_list'
    paginate_by = 10

    def get_queryset(self):

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            if direction == 'asc':
                direction = ''
            else:
                direction = '-'
            order_by = direction + order_by
        else:
            order_by = 'id'

        project_search_form = ProjectSearchForm(self.request.GET)

        if project_search_form.is_valid():
            data = project_search_form.cleaned_data
            if data.get('show_all_projects') and (self.request.user.is_superuser or self.request.user.has_perm('project.can_view_all_projects')):
                projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                    status__name__in=['Denied', ]).order_by(order_by)
            else:

                projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                    Q(status__name__in=['Denied', ]) &
                    Q(projectuser__user=self.request.user) &
                    Q(projectuser__status__name='Active')
                ).order_by(order_by)

            # Last Name
            if data.get('last_name'):
                projects = projects.filter(
                    pi__last_name__icontains=data.get('last_name'))

            # Username
            if data.get('username'):
                projects = projects.filter(
                    pi__username__icontains=data.get('username'))

            # Field of Science
            # if data.get('field_of_science'):
            #     projects = projects.filter(
            #         field_of_science__description__icontains=data.get('field_of_science'))

        else:
            projects = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
                Q(status__name__in=['Denied', ]) &
                Q(projectuser__user=self.request.user) &
                Q(projectuser__status__name='Active')
            ).order_by(order_by)

        return projects

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        projects_count = self.get_queryset().count()
        context['projects_count'] = projects_count
        context['expand'] = False

        project_search_form = ProjectSearchForm(self.request.GET)
        if project_search_form.is_valid():
            context['project_search_form'] = project_search_form
            data = project_search_form.cleaned_data
            filter_parameters = ''
            for key, value in data.items():
                if value:
                    if isinstance(value, list):
                        for ele in value:
                            filter_parameters += '{}={}&'.format(key, ele)
                    else:
                        filter_parameters += '{}={}&'.format(key, value)
            context['project_search_form'] = project_search_form
        else:
            filter_parameters = None
            context['project_search_form'] = ProjectSearchForm()

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            filter_parameters_with_order_by = filter_parameters + \
                'order_by=%s&direction=%s&' % (order_by, direction)
        else:
            filter_parameters_with_order_by = filter_parameters

        if filter_parameters:
            context['expand_accordion'] = 'show'

        context['filter_parameters'] = filter_parameters
        context['filter_parameters_with_order_by'] = filter_parameters_with_order_by

        project_list = context.get('project_list')
        paginator = Paginator(project_list, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            project_list = paginator.page(page)
        except PageNotAnInteger:
            project_list = paginator.page(1)
        except EmptyPage:
            project_list = paginator.page(paginator.num_pages)

        return context


class ProjectArchiveProjectView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_archive.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Denied', 'Waiting For Admin Approval', 'Review Pending']:
            messages.error(
                request,
                'You cannot archive a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        project = get_object_or_404(Project, pk=pk)

        context['project'] = project

        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        project = get_object_or_404(Project, pk=pk)
        project_status_archive = ProjectStatusChoice.objects.get(
            name='Archived')
        allocation_status_expired = AllocationStatusChoice.objects.get(
            name='Expired')
        end_date = datetime.datetime.now()
        project.status = project_status_archive
        project.save()
        for allocation in project.allocation_set.filter(status__name='Active'):
            allocation.status = allocation_status_expired
            allocation.end_date = end_date
            allocation.save()

        logger.info(
            f'User {request.user.username} archived a project (project pk={project.pk})'
        )
        return redirect(reverse('project-detail', kwargs={'pk': project.pk}))


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    template_name_suffix = '_create_form'
    fields = ['title', 'description', 'pi_username', 'type', ]

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        max_projects = self.request.user.userprofile.max_projects
        project_count = Project.objects.prefetch_related('pi', 'field_of_science', 'status',).filter(
            Q(pi__username=self.request.user.username) &
            Q(projectuser__status__name='Active') &
            Q(status__name__in=['New', 'Active', ])
        ).distinct().count()

        if self.request.user.is_superuser:
            return True

        # Number of projects are not being checked.
        if self.request.user.userprofile.is_pi:  # and max_projects - project_count > 0:
            return True

    def generate_slurm_account_name(self, project_obj):
        num = str(project_obj.pk)
        string = '00000'
        string = string[:-len(num)] + num
        project_type = project_obj.type.name
        letter = 'r'
        if project_type == 'Class':
            letter = 'c'

        return letter + string

    def check_max_project_type_count_reached(self, project_type_obj, pi_obj):
        limit = PROJECT_TYPE_LIMIT_MAPPING.get(project_type_obj.name)
        user_profile = UserProfile.objects.get(user=pi_obj)
        if project_type_obj.name == 'Research' and user_profile.max_research_projects_override > -1:
            limit = user_profile.max_research_projects_override
        elif project_type_obj.name == 'Class' and user_profile.max_class_projects_override > -1:
            limit = user_profile.max_class_projects_override

        if limit is not None:
            limit = int(limit)
            pi_projects_count = pi_obj.project_set.filter(
                type=project_type_obj,
                status__in=[
                    ProjectStatusChoice.objects.get(name='Active'),
                    ProjectStatusChoice.objects.get(name='Waiting For Admin Approval'),
                    ProjectStatusChoice.objects.get(name='Review Pending')
                ]).count()
            return pi_projects_count >= limit

        return False

    def form_valid(self, form):
        project_obj = form.save(commit=False)
        if not form.instance.pi_username:
            user_profile = UserProfile.objects.get(user=self.request.user)
            if user_profile.title not in ['Faculty', 'Staff', 'Academic (ACNP)',]:
                messages.error(self.request, 'Only faculty and staff can be the PI')
                return super().form_invalid(form)
            if self.check_max_project_type_count_reached(form.instance.type, self.request.user):
                messages.error(
                    self.request,
                    'You have reached the max projects you can have of this type.'
                )
                return super().form_invalid(form)
            form.instance.pi = self.request.user
        else:
            user = User.objects.filter(username=form.instance.pi_username).first()
            if user is None:
                messages.error(self.request, 'This username does not exist in RT Projects')
                return super().form_invalid(form)
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.title not in ['Faculty', 'Staff', 'Academic (ACNP)',]:
                messages.error(self.request, 'Only faculty and staff can be the PI')
                return super().form_invalid(form)
            if self.check_max_project_type_count_reached(form.instance.type, user):
                messages.error(
                    self.request,
                    'This PI has reached the max projects they can have of this type.'
                )
                return super().form_invalid(form)
            form.instance.pi = user

        form.instance.requestor = self.request.user
        form.instance.status = ProjectStatusChoice.objects.get(name='Waiting For Admin Approval')
        if form.instance.type.name == 'Class':
            if not isinstance(PROJECT_CLASS_PROJECT_END_DATES[0], tuple):
                expire_dates = [
                    tuple(map(int, x.split(':'))) for x in PROJECT_CLASS_PROJECT_END_DATES
                ]
            else:
                expire_dates = PROJECT_CLASS_PROJECT_END_DATES

            full_expire_dates = []
            for date in expire_dates:
                actual_date = datetime.date(datetime.date.today().year, date[0], date[1])
                full_expire_dates.append(actual_date)

            end_date = get_new_end_date_from_list(
                full_expire_dates,
                datetime.date.today(),
                30
            )

            if end_date is None:
                logger.error(
                    f'End date for new project request was set to None on date {datetime.date.today()}'
                )
                messages.error(
                    self.request,
                    'Something went wrong while submitting this project request. Please try again later.'
                )
                return super().form_invalid(form)

            project_obj.end_date = end_date
        else:
            actual_date = datetime.date(datetime.date.today().year, 6, 30)
            end_date = get_new_end_date_from_list(
                [actual_date, ],
                datetime.date.today(),
                PROJECT_END_DATE_CARRYOVER_DAYS
            )
            form.instance.end_date = end_date

        form.instance.max_managers = PROJECT_DEFAULT_MAX_MANAGERS
        project_obj.save()
        self.object = project_obj

        project_obj.slurm_account_name = self.generate_slurm_account_name(project_obj)
        project_obj.save()

        project_user_obj = ProjectUser.objects.create(
            user=self.request.user,
            project=project_obj,
            role=ProjectUserRoleChoice.objects.get(name='Manager'),
            status=ProjectUserStatusChoice.objects.get(name='Active')
        )
        if form.instance.pi != form.instance.requestor:
            project_user_pi_user = ProjectUser.objects.create(
                user=form.instance.pi,
                project=project_obj,
                role=ProjectUserRoleChoice.objects.get(name='Manager'),
                status=ProjectUserStatusChoice.objects.get(name='Active')
            )

        if SLACK_MESSAGING_ENABLED:
            domain_url = get_domain_url(self.request)
            project_review_url = reverse('project-review-list')
            url = '{}{}'.format(domain_url, project_review_url)
            text = f'A new request for project "{project_obj.title}" with id {project_obj.pk} has been submitted. You can view it here: {url}'
            send_message(text)
        if EMAIL_ENABLED:
            domain_url = get_domain_url(self.request)
            project_review_url = reverse('project-review-list')
            template_context = {
                'url': '{}{}'.format(domain_url, project_review_url),
                'project_title': project_obj.title,
                'project_id': project_obj.pk
            }
            send_email_template(
                'New Project Request',
                'email/new_project_request.txt',
                template_context,
                EMAIL_SENDER,
                [EMAIL_ALERTS_EMAIL_ADDRESS, ],
            )

            if form.instance.pi != form.instance.requestor:
                project_url = reverse('project-detail', kwargs={'pk': project_obj.pk})
                template_context = {
                    'center_name': EMAIL_CENTER_NAME,
                    'project_title': project_obj.title,
                    'requestor_first_name': form.instance.requestor.first_name,
                    'requestor_last_name': form.instance.requestor.last_name,
                    'requestor_username': form.instance.requestor.username,
                    'project_url': '{}{}'.format(domain_url, project_url),
                    'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                    'signature': EMAIL_SIGNATURE
                }

                send_email_template(
                    'PI For Project Request',
                    'email/pi_project_request.txt',
                    template_context,
                    EMAIL_TICKET_SYSTEM_ADDRESS,
                    [project_user_pi_user.user.email, ]
                )

                logger.info(f'Email sent to pi {form.instance.pi.username} (project pk={project_obj.pk})')

        logger.info(
            f'User {form.instance.requestor.username} created a new project (project pk={project_obj.pk})'
        )
        return super().form_valid(form)

    def reverse_with_params(self, path, **kwargs):
        return path + '?' + urllib.parse.urlencode(kwargs)

    def get_success_url(self):
        return self.reverse_with_params(
            reverse(
                'allocation-create', kwargs={'project_pk': self.object.pk}
            ),
            after_project_creation='true'
        )


class ProjectUpdateView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = ProjectUpdateForm
    template_name = 'project/project_update_form.html'
    success_message = 'Project updated.'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request,
                'You cannot update a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.kwargs.get('pk'), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_pk'] = self.kwargs.get('pk')

        return context

    def form_valid(self, form):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        form_data = form.cleaned_data

        ProjectDescriptionRecord.objects.create(
            project=project_obj,
            user=self.request.user,
            description=form_data.get('description')
        )

        project_obj.title = form_data.get('title')
        project_obj.description = form_data.get('description')
        # project_obj.field_of_science = form_data.get('field_of_science')
        project_obj.save()

        logger.info(
            f'User {self.request.user.username} updated a project (project pk={project_obj.pk})'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('pk')})


class ProjectAddUsersSearchView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_add_users.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request,
                'You cannot add users to a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['user_search_form'] = UserSearchForm()
        context['project'] = Project.objects.get(pk=self.kwargs.get('pk'))
        after_project_creation = self.request.GET.get('after_project_creation')
        if after_project_creation is None:
            after_project_creation = 'false'
        context['after_project_creation'] = after_project_creation
        return context


class ProjectAddUsersSearchResultsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/add_user_search_results.html'
    raise_exception = True

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request,
                'You cannot add users to a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_initial_data(self, request, allocations):
        initial_data = []
        for allocation in allocations:
            initial_data.append({
                'pk': allocation.pk,
                'resource': allocation.get_parent_resource.name,
                'resource_type': allocation.get_parent_resource.resource_type.name,
                'status': allocation.status.name
            })

        return initial_data

    def get_disable_select_list(self, request, allocations):
        """
        Gets a list that determines if an allocation can be selected.
        """
        disable_select_list = [False] * len(allocations)
        for i, allocation in enumerate(allocations):
            if allocation.get_parent_resource.name == 'Slate-Project':
                if allocation.data_manager != request.user.username:
                    disable_select_list[i] = True

        return disable_select_list

    def post(self, request, *args, **kwargs):
        user_search_string = request.POST.get('q')
        search_by = request.POST.get('search_by')
        pk = self.kwargs.get('pk')
        after_project_creation = request.POST.get('after_project_creation')
        if after_project_creation is None:
            after_project_creation = 'false'

        project_obj = get_object_or_404(Project, pk=pk)

        users_to_exclude = [ele.user.username for ele in project_obj.projectuser_set.filter(
            status__name='Active')]

        cobmined_user_search_obj = CombinedUserSearch(
            user_search_string, search_by, users_to_exclude)

        context = cobmined_user_search_obj.search()
        context['after_project_creation'] = after_project_creation

        ldap_user_info_enabled = False
        if 'coldfront.plugins.ldap_user_info' in settings.INSTALLED_APPS:
            from coldfront.plugins.ldap_user_info.utils import get_user_info
            ldap_user_info_enabled = True

        # Initial data for ProjectAddUserForm
        matches = context.get('matches')
        for match in matches:
            if ldap_user_info_enabled and get_user_info(match.get('username'), ['title'])['title'][0] == 'group':
                match.update({'role': ProjectUserRoleChoice.objects.get(name='Group')})
            else:
                match.update({'role': ProjectUserRoleChoice.objects.get(name='User')})

        if matches:
            formset = formset_factory(ProjectAddUserForm, max_num=len(matches))
            formset = formset(initial=matches, prefix='userform')
            context['formset'] = formset
            context['user_search_string'] = user_search_string
            context['search_by'] = search_by

        if len(user_search_string.split()) > 1:
            users_already_in_project = []
            for ele in user_search_string.split():
                if ele in users_to_exclude:
                    users_already_in_project.append(ele)
            context['users_already_in_project'] = users_already_in_project

        status_list = ['Active', 'New', 'Renewal Requested', 'Billing Information Submitted']
        allocations = project_obj.allocation_set.filter(
            status__name__in=status_list,
            allocationuser__user=request.user
        )
        initial_data = self.get_initial_data(request, allocations)

        help_text = 'Select allocations to add selected users to. If a user does not have an account on a resource in an allocation they will not be added.'
        for allocation_info in initial_data:
            if allocation_info['resource'] == 'Slate-Project':
                help_text += ' Only Slate-Project allocations you are a data manager of can be selected.'
                break

        allocation_formset = formset_factory(
            ProjectAddUsersToAllocationForm,
            max_num=len(initial_data),
            formset=ProjectFormSetWithSelectDisabled
        )
        allocation_formset = allocation_formset(
            initial=initial_data,
            prefix="allocationform",
            form_kwargs={
                'disable_selected': self.get_disable_select_list(request, allocations)
            }
        )

        # The following block of code is used to hide/show the allocation div in the form.
        if initial_data:
            div_allocation_class = 'placeholder_div_class'
        else:
            div_allocation_class = 'd-none'
        context['div_allocation_class'] = div_allocation_class
        ###

        context['pk'] = pk
        context['help_text'] = help_text
        context['allocation_form'] = allocation_formset
        context['current_num_managers'] = project_obj.get_current_num_managers()
        context['max_managers'] = project_obj.max_managers
        return render(request, self.template_name, context)


class ProjectAddUsersView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request,
                'You cannot add users to a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_initial_data(self, request, allocations):
        initial_data = []
        for allocation in allocations:
            initial_data.append({
                'pk': allocation.pk,
                'resource': allocation.get_parent_resource.name,
                'resource_type': allocation.get_parent_resource.resource_type.name,
                'status': allocation.status.name
            })

        return initial_data

    def get_disable_select_list(self, request, allocations):
        """
        Gets a list that determines if an allocation can be selected.
        """
        disable_select_list = [False] * len(allocations)
        for i, allocation in enumerate(allocations):
            if allocation.get_parent_resource.name == 'Slate-Project':
                if allocation.data_manager != request.user.username:
                    disable_select_list[i] = True

        return disable_select_list

    def post(self, request, *args, **kwargs):
        user_search_string = request.POST.get('q')
        search_by = request.POST.get('search_by')
        pk = self.kwargs.get('pk')
        after_project_creation = request.POST.get('after_project_creation')

        project_obj = get_object_or_404(Project, pk=pk)

        users_to_exclude = [ele.user.username for ele in project_obj.projectuser_set.filter(
            status__name='Active')]

        cobmined_user_search_obj = CombinedUserSearch(
            user_search_string, search_by, users_to_exclude)

        context = cobmined_user_search_obj.search()

        ldap_user_info_enabled = False
        if 'coldfront.plugins.ldap_user_info' in settings.INSTALLED_APPS:
            from coldfront.plugins.ldap_user_info.utils import get_user_info
            ldap_user_info_enabled = True

        # Initial data for ProjectAddUserForm
        matches = context.get('matches')
        for match in matches:
            if ldap_user_info_enabled and get_user_info(match.get('username'), ['title'])['title'][0] == 'group':
                match.update({'role': ProjectUserRoleChoice.objects.get(name='Group')})
            else:
                match.update({'role': ProjectUserRoleChoice.objects.get(name='User')})

        formset = formset_factory(ProjectAddUserForm, max_num=len(matches))
        formset = formset(request.POST, initial=matches, prefix='userform')

        status_list = ['Active', 'New', 'Renewal Requested', 'Billing Information Submitted']
        allocations = project_obj.allocation_set.filter(
            status__name__in=status_list,
            allocationuser__user=request.user
        )
        initial_data = self.get_initial_data(request, allocations)

        allocation_formset = formset_factory(
            ProjectAddUsersToAllocationForm,
            max_num=len(initial_data),
            formset=ProjectFormSetWithSelectDisabled
        )
        allocation_formset = allocation_formset(
            request.POST,
            initial=initial_data,
            prefix="allocationform",
            form_kwargs={
                'disable_selected': self.get_disable_select_list(request, allocations)
            }
        )

        added_users_count = 0
        added_users_emails = []
        added_users = []
        allocations_added_to = {}
        display_warning = False
        if formset.is_valid() and allocation_formset.is_valid():
            project_user_active_status_choice = ProjectUserStatusChoice.objects.get(
                name='Active')
            allocation_user_status_choice = AllocationUserStatusChoice.objects.get(
                name='Active')

            no_accounts = {}
            managers_rejected = []
            resources_requiring_user_request = {}
            requestor_user = User.objects.get(username=request.user)
            for form in formset:
                user_form_data = form.cleaned_data

                if user_form_data['selected']:
                    added_users_count += 1

                    # Will create local copy of user if not already present in local database
                    user_obj, _ = User.objects.get_or_create(
                        username=user_form_data.get('username'))
                    user_obj.first_name = user_form_data.get('first_name')
                    user_obj.last_name = user_form_data.get('last_name')
                    user_obj.email = user_form_data.get('email')
                    user_obj.save()

                    role_choice = user_form_data.get('role')

                    # If no more managers can be added then give the user the 'User' role.
                    if role_choice.name == 'Manager':
                        if project_obj.check_exceeds_max_managers(1):
                            role_choice = ProjectUserRoleChoice.objects.get(name='User')
                            managers_rejected.append(user_form_data.get('username'))

                    # Is the user already in the project?
                    if project_obj.projectuser_set.filter(user=user_obj).exists():
                        project_user_obj = project_obj.projectuser_set.get(
                            user=user_obj)
                        project_user_obj.role = role_choice
                        project_user_obj.status = project_user_active_status_choice
                        project_user_obj.save()
                    else:
                        project_user_obj = ProjectUser.objects.create(
                            user=user_obj, project=project_obj, role=role_choice, status=project_user_active_status_choice)

                    # Notifications by default will be disabled for group accounts.
                    if role_choice.name == 'Group':
                        project_user_obj.enable_notifications = False
                        project_user_obj.save()

                    if project_user_obj.enable_notifications:
                        added_users_emails.append(user_obj.email)

                    added_users.append(user_obj.username)

                    username = user_form_data.get('username')
                    no_accounts[username] = []
                    for allocation in allocation_formset:
                        cleaned_data = allocation.cleaned_data
                        if cleaned_data['selected']:
                            allocation = allocations.get(pk=cleaned_data['pk'])
                            if allocations_added_to.get(allocation) is None:
                                # First list is users added, second list is users added emails
                                allocations_added_to[allocation] = [[], []]

                            resource_name = allocation.get_parent_resource.name
                            # If the user does not have an account on the resource in the allocation then do not add them to it.
                            if not allocation.check_user_account_exists_on_resource(username):
                                display_warning = True
                                # Make sure there are no duplicates for a user if there's more than one instance of a resource.
                                if allocation.get_parent_resource.get_attribute('check_user_account') not in no_accounts[username]:
                                    no_accounts[username].append(allocation.get_parent_resource.get_attribute('check_user_account'))
                                continue

                            requires_user_request = allocation.get_parent_resource.get_attribute(
                                'requires_user_request'
                            )
                            if requires_user_request is not None and requires_user_request == 'Yes':
                                resources_requiring_user_request.setdefault(resource_name, set())
                                resources_requiring_user_request[resource_name].add(username)

                                allocation_user_status_choice = AllocationUserStatusChoice.objects.get(
                                    name='Pending - Add'
                                )

                            if allocation.allocationuser_set.filter(user=user_obj).exists():
                                allocation_user_obj = allocation.allocationuser_set.get(
                                    user=user_obj)
                                allocation_user_obj.status = allocation_user_status_choice
                                allocation_user_obj.save()
                            else:
                                allocation_user_obj = AllocationUser.objects.create(
                                    allocation=allocation,
                                    user=user_obj,
                                    status=allocation_user_status_choice)
                            allocation_activate_user.send(sender=self.__class__,
                                                        allocation_user_pk=allocation_user_obj.pk)

                            requires_user_request = allocation.get_parent_resource.get_attribute(
                                'requires_user_request'
                            )

                            allocation_user_request_obj = allocation.create_user_request(
                                requestor_user=requestor_user,
                                allocation_user=allocation_user_obj,
                                allocation_user_status=allocation_user_status_choice

                            )

                            if allocation_user_request_obj is None:
                                allocations_added_to[allocation][0].append(user_obj.username)
                                if project_user_obj.enable_notifications:
                                    allocations_added_to[allocation][1].append(user_obj.email)

            if display_warning:
                warning_message = 'The following users were not added to the selected resources due to missing accounts:<ul>'
                for username, no_account_list in no_accounts.items():
                    warning_message += '<li>{} is missing an account for {}</li>'.format(
                        username,
                        ', '.join(no_account_list)
                    )
                warning_message += '</ul>'
                if warning_message != '':
                    warning_message += 'They cannot be added until they create one. Please direct them to <a href="https://access.iu.edu/Accounts/Create">https://access.iu.edu/Accounts/Create</a> to create one.'

                    messages.warning(
                        request, format_html(warning_message)
                    )

            if EMAIL_ENABLED and added_users:
                added_users_emails.append(project_obj.pi.email)

                domain_url = get_domain_url(self.request)
                project_url = '{}{}'.format(domain_url, reverse(
                    'project-detail', kwargs={'pk': project_obj.pk}))

                template_context = {
                    'center_name': EMAIL_CENTER_NAME,
                    'project_title': project_obj.title,
                    'users': added_users,
                    'url': project_url,
                    'signature': EMAIL_SIGNATURE
                }
                send_email_template(
                    'Added to Project',
                    'email/project_added_users.txt',
                    template_context,
                    EMAIL_TICKET_SYSTEM_ADDRESS,
                    added_users_emails
                )

                if allocations_added_to:
                    for allocation, values in allocations_added_to.items():
                        allocations_added_users = values[0]
                        allocations_added_users_emails = values[1]
                        if allocations_added_users:
                            if project_obj.pi.email not in allocations_added_users_emails:
                                allocations_added_users_emails.append(project_obj.pi.email)

                        logger.info(
                            f'User {request.user.username} added {len(allocations_added_users)} user(s) to a '
                            f'{allocation.get_parent_resource.name} allocation (allocation pk={allocation.pk})'
                        )
                        send_added_user_email(
                            request,
                            allocation,
                            allocations_added_users,
                            allocations_added_users_emails
                        )

            logger.info(
                f'User {request.user.username} added {added_users_count} user(s) to a project '
                f'(project pk={project_obj.pk})'
            )
            messages.success(
                request, 'Added {} users to project.'.format(added_users_count))
        else:
            if not formset.is_valid():
                for error in formset.errors:
                    messages.error(request, error)

            if not allocation_formset.is_valid():
                for error in allocation_formset.errors:
                    messages.error(request, error)

        if after_project_creation == 'true':
            return HttpResponseRedirect(
                self.reverse_with_params(
                    reverse(
                        'project-detail', kwargs={'pk': pk}
                    ),
                    after_project_creation='true'
                )
            )

        return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': pk}))
    
    def reverse_with_params(self, path, **kwargs):
        return path + '?' + urllib.parse.urlencode(kwargs)


class ProjectRemoveUsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_remove_users.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request,
                'You cannot remove users from a project with status "{}".'.format(project_obj.status.name)
            )
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_users_to_remove(self, project_obj):
        users_to_remove = [

            {'username': ele.user.username,
             'first_name': ele.user.first_name,
             'last_name': ele.user.last_name,
             'email': ele.user.email,
             'role': ele.role}

            for ele in project_obj.projectuser_set.filter(status__name='Active').order_by('user__username') if ele.user != self.request.user and ele.user != project_obj.pi
        ]

        return users_to_remove

    def get_data_managers(self, project_obj):
        data_manager_list = [
            allocation.data_manager for allocation in project_obj.allocation_set.filter(
                resources__name="Slate-Project"
            )
        ]

        return set(data_manager_list)

    def get_disable_select_list(self, project_obj, users_to_remove):
        """
        Gets a list that determines if a user can be removed by disabling the
        ProjectRemoveUserForm's selected field.
        """
        data_manager_list = self.get_data_managers(project_obj)
        disable_select_list = [False] * len(users_to_remove)
        for i, user in enumerate(users_to_remove):
            if user['username'] in data_manager_list:
                disable_select_list[i] = True

        return disable_select_list

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)

        users_to_remove = self.get_users_to_remove(project_obj)
        context = {}

        if users_to_remove:
            formset = formset_factory(
                ProjectRemoveUserForm,
                max_num=len(users_to_remove),
                formset=ProjectRemoveUserFormset
            )

            formset = formset(
                initial=users_to_remove,
                prefix='userform',
                form_kwargs={
                    'disable_selected': self.get_disable_select_list(project_obj, users_to_remove)
                }
            )

            context['formset'] = formset

        context['data_managers'] = self.get_data_managers(project_obj)
        context['project'] = get_object_or_404(Project, pk=pk)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)

        users_to_remove = self.get_users_to_remove(project_obj)

        formset = formset_factory(
            ProjectRemoveUserForm,
            max_num=len(users_to_remove),
            formset=ProjectRemoveUserFormset
        )

        formset = formset(
            request.POST,
            initial=users_to_remove,
            prefix='userform',
            form_kwargs={
                'disable_selected': self.get_disable_select_list(project_obj, users_to_remove)
            }
        )

        remove_users_count = 0
        removed_users_emails = []
        removed_users = []
        if formset.is_valid():
            project_user_removed_status_choice = ProjectUserStatusChoice.objects.get(
                name='Removed')
            allocation_user_removed_status_choice = AllocationUserStatusChoice.objects.get(
                name='Removed')

            resources_requiring_user_request = {}
            for form in formset:
                user_form_data = form.cleaned_data
                if user_form_data['selected']:
                    user_obj = User.objects.get(
                        username=user_form_data.get('username'))

                    if project_obj.pi == user_obj:
                        continue

                    remove_user_from_project = True

                    # get allocation to remove users from
                    allocations_to_remove_user_from = project_obj.allocation_set.filter(
                        status__name__in=['Active', 'New', 'Renewal Requested'])
                    for allocation in allocations_to_remove_user_from:
                        for allocation_user_obj in allocation.allocationuser_set.filter(user=user_obj, status__name__in=['Active', 'Pending - Add', 'Pending - Remove']):
                            resource = allocation.get_parent_resource
                            requires_user_requests = resource.get_attribute(
                                'requires_user_request'
                            )

                            # Users will still be removed from allocations that do not require a
                            # user review.
                            if requires_user_requests is not None and requires_user_requests == 'Yes':
                                resources_requiring_user_request.setdefault(resource.name, set())
                                resources_requiring_user_request[resource.name].add(
                                    allocation_user_obj.user.username
                                )
                                remove_user_from_project = False
                                continue

                            allocation_user_obj.status = allocation_user_removed_status_choice
                            allocation_user_obj.save()

                            allocation_remove_user.send(sender=self.__class__,
                                                        allocation_user_pk=allocation_user_obj.pk)

                    if remove_user_from_project:
                        remove_users_count += 1
                        project_user_obj = project_obj.projectuser_set.get(
                            user=user_obj)
                        project_user_obj.status = project_user_removed_status_choice
                        project_user_obj.save()

                        if project_user_obj.enable_notifications:
                            removed_users_emails.append(user_obj.email)

                        removed_users.append(user_obj.username)

            if remove_users_count:
                if EMAIL_ENABLED:
                    removed_users_emails.append(project_obj.pi.email)

                    template_context = {
                        'center_name': EMAIL_CENTER_NAME,
                        'project_title': project_obj.title,
                        'users': removed_users,
                        'signature': EMAIL_SIGNATURE
                    }
                    send_email_template(
                        'Removed From Project',
                        'email/project_removed_users.txt',
                        template_context,
                        EMAIL_TICKET_SYSTEM_ADDRESS,
                        removed_users_emails
                    )

                logger.info(
                    f'User {request.user.username} removed {remove_users_count} user(s) from a '
                    f'project (project pk={project_obj.pk})'
                )

                if remove_users_count == 1:
                    messages.success(
                        request, 'Removed {} user from project.'.format(remove_users_count))
                else:
                    messages.success(
                        request, 'Removed {} users from project.'.format(remove_users_count))

            for resource_name, users in resources_requiring_user_request.items():
                messages.warning(
                    request, 'User(s) {} in resource {} must be removed from the allocation first.'
                    .format(', '.join(users), resource_name)
                )
        else:
            for error in formset.errors:
                messages.error(request, error)

        return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': pk}))


class ProjectUserDetail(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_user_detail.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

    def check_user_is_data_manager(self, project_obj, project_user_obj):
        data_manager_list = [
            allocation.data_manager for allocation in project_obj.allocation_set.filter(
                resources__name="Slate-Project"
            )
        ]

        if project_user_obj.user.username in set(data_manager_list):
            return True

        return False

    def check_user_is_manager(self, project_user_obj):
        if project_user_obj.role == ProjectUserRoleChoice.objects.get(name='Manager'):
            return True

        return False

    def get(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        project_user_pk = self.kwargs.get('project_user_pk')

        if project_obj.projectuser_set.filter(pk=project_user_pk).exists():
            project_user_obj = project_obj.projectuser_set.get(
                pk=project_user_pk)

            is_data_manager = self.check_user_is_data_manager(project_obj, project_user_obj)
            is_manager = self.check_user_is_manager(project_user_obj)
            project_user_update_form = ProjectUserUpdateForm(
                initial={
                    'role': project_user_obj.role,
                    'enable_notifications': project_user_obj.enable_notifications
                },
                disable_role=is_data_manager,
                disable_enable_notifications=is_manager
            )

            context = {}
            context['project_obj'] = project_obj
            context['project_user_update_form'] = project_user_update_form
            context['project_user_obj'] = project_user_obj
            context['is_data_manager'] = is_data_manager

            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        project_user_pk = self.kwargs.get('project_user_pk')

        if project_obj.status.name in ['Archived', 'Denied', 'Expired', ]:
            messages.error(
                request, 'You cannot update a user in a(n) {} project.'.format(project_obj.status.name))
            return HttpResponseRedirect(reverse('project-user-detail', kwargs={'pk': project_user_pk}))

        if project_obj.projectuser_set.filter(id=project_user_pk).exists():
            project_user_obj = project_obj.projectuser_set.get(
                pk=project_user_pk)

            if project_user_obj.user == project_user_obj.project.pi:
                messages.error(
                    request, 'PI role and email notification option cannot be changed.')
                return HttpResponseRedirect(reverse('project-user-detail', kwargs={'pk': project_user_pk}))

            is_data_manager = self.check_user_is_data_manager(project_obj, project_user_obj)
            is_manager = self.check_user_is_manager(project_user_obj)
            project_user_update_form = ProjectUserUpdateForm(
                request.POST,
                initial={
                    'role': project_user_obj.role.name,
                    'enable_notifications': project_user_obj.enable_notifications
                },
                disable_role=is_data_manager,
                disable_enable_notifications=is_manager
            )

            # If nothing has changed then don't update it.
            if is_data_manager:
                return HttpResponseRedirect(reverse('project-user-detail', kwargs={'pk': project_obj.pk, 'project_user_pk': project_user_obj.pk}))

            if project_user_update_form.is_valid():
                form_data = project_user_update_form.cleaned_data
                enable_notifications = form_data.get('enable_notifications')
                if form_data.get('role').name == 'Manager':
                    enable_notifications = True
                    if project_user_obj.role.name != 'Manager':
                        if project_obj.get_current_num_managers() >= project_obj.max_managers:
                            messages.error(
                                request,
                                """
                                This project is at its maximum Managers limit ({}) and cannot have
                                more.
                                """.format(project_obj.max_managers)
                            )
                            return HttpResponseRedirect(
                                reverse(
                                    'project-user-detail',
                                    kwargs={
                                        'pk': project_obj.pk,
                                        'project_user_pk': project_user_obj.pk
                                    }
                                )
                            )

                project_user_obj.enable_notifications = enable_notifications
                project_user_obj.role = ProjectUserRoleChoice.objects.get(
                    name=form_data.get('role'))
                project_user_obj.save()

                logger.info(
                    f'User {request.user.username} updated {project_user_obj.user.username}\'s '
                    f'role (project pk={project_obj.pk})'
                )

                messages.success(request, 'User details updated.')
                return HttpResponseRedirect(reverse('project-user-detail', kwargs={'pk': project_obj.pk, 'project_user_pk': project_user_obj.pk}))
            else:
                messages.error(request, project_user_update_form.errors)
                return HttpResponseRedirect(reverse('project-user-detail', kwargs={'pk': project_obj.pk, 'project_user_pk': project_user_obj.pk}))


@login_required
def project_update_email_notification(request):

    if request.method == "POST":
        data = request.POST
        project_user_obj = get_object_or_404(
            ProjectUser, pk=data.get('user_project_id'))

        project_obj = project_user_obj.project

        allowed = False
        if project_obj.pi == request.user:
            allowed = True

        if project_obj.projectuser_set.filter(user=request.user, role__name='Manager', status__name='Active').exists():
            allowed = True

        if project_user_obj.user == request.user:
            allowed = True

        if request.user.is_superuser:
            allowed = True

        if allowed is False:
            return HttpResponse('not allowed', status=403)
        else:
            checked = data.get('checked')
            if checked == 'true':
                project_user_obj.enable_notifications = True
                project_user_obj.save()
                return HttpResponse('checked', status=200)
            elif checked == 'false':
                project_user_obj.enable_notifications = False
                project_user_obj.save()
                return HttpResponse('unchecked', status=200)
            else:
                return HttpResponse('no checked', status=400)
    else:
        return HttpResponse('no POST', status=400)


class ProjectReviewView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_review.html'
    login_url = "/"  # redirect URL if fail test_func

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

        messages.error(
            self.request, 'You do not have permissions to review this project.')

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))

        if not project_obj.needs_review and not project_obj.can_be_reviewed:
            messages.error(request, 'You do not need to review this project.')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

        if 'Auto-Import Project'.lower() in project_obj.title.lower():
            messages.error(
                request, 'You must update the project title before reviewing your project. You cannot have "Auto-Import Project" in the title.')
            return HttpResponseRedirect(reverse('project-update', kwargs={'pk': project_obj.pk}))

        if 'We do not have information about your research. Please provide a detailed description of your work and update your field of science. Thank you!' in project_obj.description:
            messages.error(
                request, 'You must update the project description before reviewing your project.')
            return HttpResponseRedirect(reverse('project-update', kwargs={'pk': project_obj.pk}))

        return super().dispatch(request, *args, **kwargs)

    def get_allocation_data(self, project_obj):
        allocations = project_obj.allocation_set.filter(
            status__name__in=['Active', 'Expired', ],
            resources__requires_payment=False
        ).exclude(use_indefinitely=True)
        initial_data = []
        if allocations:
            for allocation in allocations:
                if allocation.end_date is None:
                    continue
                if allocation.expires_in < -ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING:
                    continue

                data = {
                    'pk': allocation.pk,
                    'resource': allocation.get_resources_as_string,
                    'users': ', '.join(
                        [
                            '{} {}'.format(
                                ele.user.first_name, ele.user.last_name
                            ) for ele in allocation.allocationuser_set.filter(
                                status__name='Active'
                            ).order_by('user__last_name')
                        ]
                    ),
                    'status': allocation.status,
                    'expires_on': allocation.end_date,
                    'renew': False
                }
                initial_data.append(data)

        return initial_data

    def get(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        project_review_form = ProjectReviewForm()

        context = {}
        context['project'] = project_obj
        context['project_review_form'] = project_review_form
        context['project_users'] = ', '.join(['{} {}'.format(ele.user.first_name, ele.user.last_name)
                                              for ele in project_obj.projectuser_set.filter(status__name='Active').order_by('user__last_name')])

        context['formset'] = []
        allocation_data = self.get_allocation_data(project_obj)
        if allocation_data:
            formset = formset_factory(ProjectReviewAllocationForm, max_num=len(allocation_data))
            formset = formset(initial=allocation_data, prefix='allocationform')
            context['formset'] = formset

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        project_review_form = ProjectReviewForm(request.POST)

        project_review_status_choice = ProjectReviewStatusChoice.objects.get(
            name='Pending')
        project_status_choice = ProjectStatusChoice.objects.get(name="Review Pending")

        allocation_renewals = []
        if project_review_form.is_valid():
            allocation_data = self.get_allocation_data(project_obj)
            if allocation_data:
                formset = formset_factory(ProjectReviewAllocationForm, max_num=len(allocation_data))
                formset = formset(request.POST, initial=allocation_data, prefix='allocationform')

                if formset.is_valid():
                    allocation_status_choice = AllocationStatusChoice.objects.get(name="Renewal Requested")
                    for form in formset:
                        data = form.cleaned_data
                        if data.get('renew'):
                            allocation_renewals.append(str(data.get('pk')))
                            allocation = Allocation.objects.get(pk=data.get('pk'))
                            allocation.status = allocation_status_choice
                            allocation.save()
                else:
                    logger.error(
                        f'There was an error submitting allocation renewals for PI '
                        f'{project_obj.pi.username} (project pk={project_obj.pk})'
                    )
                    messages.error(
                        request, 'There was an error submitting your allocation renewals.'
                    )
                    return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

            form_data = project_review_form.cleaned_data
            project_updates = form_data.get('project_updates')
            if form_data.get('no_project_updates'):
                project_updates = 'No new project updates.'

            project_review_obj = ProjectReview.objects.create(
                project=project_obj,
                project_updates=project_updates,
                allocation_renewals=','.join(allocation_renewals),
                status=project_review_status_choice)

            project_obj.force_review = False
            project_obj.status = project_status_choice
            project_obj.save()

            domain_url = get_domain_url(self.request)
            url = '{}{}'.format(domain_url, reverse('project-review-list'))

            if EMAIL_ENABLED:
                send_email_template(
                    'New project renewal has been submitted',
                    'email/new_project_renewal.txt',
                    {
                        'url': url,
                        'project_title': project_obj.title,
                        'project_id': project_obj.pk
                    },
                    EMAIL_SENDER,
                    [EMAIL_ALERTS_EMAIL_ADDRESS, ]
                )

            logger.info(
                f'User {request.user.username} submitted a project renewal (project pk={project_obj.pk})'
            )

            messages.success(request, 'Project review submitted.')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            messages.error(
                request, 'There was an error in processing your project review.')

            errors = project_review_form.errors.get('__all__')
            if errors and len(errors):
                for error in errors:
                    messages.error(request, error)

            return HttpResponseRedirect(reverse('project-review', kwargs={'pk': project_obj.pk}))


class ProjectReviewListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_review_list.html'
    login_url = '/'

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_review_pending_projects'):
            return True

        messages.error(
            self.request, 'You do not have permission to review pending project reviews/requests.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_review_list'] = ProjectReview.objects.filter(status__name='Pending')
        projects = Project.objects.filter(
            status__name="Waiting For Admin Approval"
        )
        context['project_request_list'] = projects
        pis = set()
        for project in projects:
            pis.add(project.pi)
        
        pi_project_objs = Project.objects.filter(
            pi__in=pis,
            status__name='Active'
        )
        pi_projects = []
        for pi_project_obj in pi_project_objs:
            pi_projects.append(
                {
                    'title': pi_project_obj.title,
                    'pi': pi_project_obj.pi.username,
                    'description': pi_project_obj.description,
                    'display': 'false' 
                }
            )
        context['pi_projects'] = pi_projects

        context['EMAIL_ENABLED'] = EMAIL_ENABLED
        return context


class ProjectActivateRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = '/'

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not self.request.user.is_superuser:
            if not self.request.user.has_perm('project.can_review_pending_projects'):
                return False

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name != 'Waiting For Admin Approval':
            messages.error(
                self.request, f'You cannot approve a project with status "{project_obj.status.name}"'
            )
            return False

        return True

    def get(self, request, pk):
        project_obj = get_object_or_404(Project, pk=pk)
        project_status_obj = ProjectStatusChoice.objects.get(name="Active")

        create_admin_action(request.user, {'status': project_status_obj}, project_obj)

        project_obj.status = project_status_obj
        project_obj.save()

        messages.success(request, 'Project request for {} has been APPROVED'.format(
            project_obj.title))

        if EMAIL_ENABLED:
            domain_url = get_domain_url(self.request)
            project_url = '{}{}'.format(domain_url, reverse(
                'project-detail', kwargs={'pk': project_obj.pk}
            ))

            template_context = {
                'project_title': project_obj.title,
                'project_url': project_url,
                'signature': EMAIL_SIGNATURE,
                'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                'center_name': EMAIL_CENTER_NAME
            }

            email_receiver_list = get_project_user_emails(project_obj)
            send_email_template(
                'Your Project Request Was Approved',
                'email/project_request_approved.txt',
                template_context,
                EMAIL_TICKET_SYSTEM_ADDRESS,
                email_receiver_list
            )

        logger.info(
            f'Admin {request.user.username} approved a project request (project pk={project_obj.pk})'
        )
        return HttpResponseRedirect(reverse('project-review-list'))


class ProjectDenyRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = '/'

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not self.request.user.is_superuser:
            if not self.request.user.has_perm('project.can_review_pending_projects'):
                return False

        project_obj = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        if project_obj.status.name != 'Waiting For Admin Approval':
            messages.error(
                self.request, f'You cannot deny a project with status "{project_obj.status.name}"'
            )
            return False

        return True

    def get(self, request, pk):
        project_obj = get_object_or_404(Project, pk=pk)
        project_status_obj = ProjectStatusChoice.objects.get(name="Denied")

        create_admin_action(request.user, {'status': project_status_obj}, project_obj)

        project_obj.status = project_status_obj

        free_allocation_obj_list = project_obj.allocation_set.filter(status__name__in=['Active', 'New', 'Renewal Requested'])
        allocation_status_obj = AllocationStatusChoice.objects.get(name="Denied")
        for allocation in free_allocation_obj_list:
            allocation.status = allocation_status_obj
            allocation.save()

        paid_allocation_obj_list = project_obj.allocation_set.filter(status__name__in=['Payment Requested', 'Payment Pending', 'Paid'])
        allocation_status_obj = AllocationStatusChoice.objects.get(name="Payment Declined")
        for allocation in paid_allocation_obj_list:
            allocation.status = allocation_status_obj
            allocation.save()

        project_obj.save()

        messages.success(request, 'Project request for {} has been DENIED'.format(
            project_obj.title))

        if EMAIL_ENABLED:
            domain_url = get_domain_url(self.request)
            project_url = '{}{}'.format(domain_url, reverse(
                'project-detail', kwargs={'pk': project_obj.pk}
            ))

            template_context = {
                'project_title': project_obj.title,
                'project_url': project_url,
                'signature': EMAIL_SIGNATURE,
                'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                'center_name': EMAIL_CENTER_NAME
            }

            email_receiver_list = get_project_user_emails(project_obj, True)
            
            send_email_template(
                'Your Project Request Was Denied',
                'email/project_request_denied.txt',
                template_context,
                EMAIL_TICKET_SYSTEM_ADDRESS,
                email_receiver_list
            )

        logger.info(
            f'Admin {request.user.username} denied a project request (project pk={project_obj.pk})'
        )
        return HttpResponseRedirect(reverse('project-review-list'))


class ProjectReviewApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not self.request.user.is_superuser:
            if not self.request.user.has_perm('project.can_review_pending_projects'):
                return False

        project_review_obj = get_object_or_404(ProjectReview, pk=self.kwargs.get('pk'))
        if project_review_obj.status.name != 'Pending':
            messages.error(
                self.request, f'You cannot approve a project review with status "{project_review_obj.status.name}"'
            )
            return False

        return True

    def get(self, request, pk):
        project_review_obj = get_object_or_404(ProjectReview, pk=pk)
        project_review_status_obj = ProjectReviewStatusChoice.objects.get(name="Approved")
        project_obj = project_review_obj.project
        project_status_obj = ProjectStatusChoice.objects.get(name="Active")

        if project_obj.type.name == 'Class':
            if not isinstance(PROJECT_CLASS_PROJECT_END_DATES[0], tuple):
                expire_dates = [
                    tuple(map(int, x.split(':'))) for x in PROJECT_CLASS_PROJECT_END_DATES
                ]
            else:
                expire_dates = PROJECT_CLASS_PROJECT_END_DATES

            full_expire_dates = []
            for date in expire_dates:
                actual_date = datetime.date(datetime.date.today().year, date[0], date[1])
                full_expire_dates.append(actual_date)

            end_date = get_new_end_date_from_list(
                full_expire_dates,
                project_review_obj.created.date(),
                30
            )

            if end_date is None:
                logger.error(
                    f'New end date for project {project_obj.title} was set to None with project '
                    f'review creation date {project_review_obj.created.date()} during project '
                    f'review approval'
                )
                messages.error(request, 'Something went wrong while approving the review.')
                return HttpResponseRedirect(reverse('project-review-list'))

            project_obj.end_date = end_date
        else:
            actual_date = datetime.date(datetime.date.today().year, 6, 30)
            end_date = get_new_end_date_from_list(
                [actual_date, ],
                datetime.date.today(),
                PROJECT_DAYS_TO_REVIEW_BEFORE_EXPIRING
            )
            project_obj.end_date = end_date

        create_admin_action(request.user, {'status': project_status_obj}, project_obj)

        project_review_obj.status = project_review_status_obj
        project_obj.status = project_status_obj

        if project_review_obj.allocation_renewals:
            allocation_status_choice = AllocationStatusChoice.objects.get(name="Active")
            for allocation_pk in project_review_obj.allocation_renewals.split(','):
                allocation = Allocation.objects.get(pk=int(allocation_pk))
                allocation.start_date = datetime.datetime.today()
                allocation.end_date = project_obj.end_date
                allocation.status = allocation_status_choice
                allocation.save()

        project_review_obj.save()
        project_obj.save()

        messages.success(request, 'Project review for {} has been APPROVED'.format(
            project_review_obj.project.title)
        )

        if EMAIL_ENABLED:
            domain_url = get_domain_url(self.request)
            project_url = '{}{}'.format(domain_url, reverse(
                'project-detail', kwargs={'pk': project_review_obj.project.pk}
            ))
            renewed_allocation_urls = []
            if project_review_obj.allocation_renewals:
                for allocation_pk in project_review_obj.allocation_renewals.split(','):
                    allocation_url = '{}{}'.format(domain_url, reverse(
                        'allocation-detail', kwargs={'pk': allocation_pk}
                    ))
                    renewed_allocation_urls.append(allocation_url)

            template_context = {
                'project_title': project_review_obj.project.title,
                'project_url': project_url,
                'signature': EMAIL_SIGNATURE,
                'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                'center_name': EMAIL_CENTER_NAME,
                'renewed_allocation_urls': renewed_allocation_urls
            }

            email_receiver_list = get_project_user_emails(project_obj)
            send_email_template(
                'Your Project Renewal Was Approved',
                'email/project_renewal_approved.txt',
                template_context,
                EMAIL_TICKET_SYSTEM_ADDRESS,
                email_receiver_list
            )

        logger.info(
            f'Admin {request.user.username} approved a project renewal request (project pk={project_obj.pk})'
        )
        return HttpResponseRedirect(reverse('project-review-list'))


class ProjectReviewDenyView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not self.request.user.is_superuser:
            if not self.request.user.has_perm('project.can_review_pending_projects'):
                return False

        project_review_obj = get_object_or_404(ProjectReview, pk=self.kwargs.get('pk'))
        if project_review_obj.status.name != 'Pending':
            messages.error(
                self.request, f'You cannot deny a project review with status "{project_review_obj.status.name}"'
            )
            return False

        return True

    def get(self, request, pk):
        project_review_obj = get_object_or_404(ProjectReview, pk=pk)
        project_review_status_obj = ProjectReviewStatusChoice.objects.get(name="Denied")
        project_obj = project_review_obj.project
        project_status_obj = ProjectStatusChoice.objects.get(name="Denied")

        create_admin_action(request.user, {'status': project_status_obj}, project_obj)

        project_review_obj.status = project_review_status_obj
        project_obj.status = project_status_obj

        if project_review_obj.allocation_renewals:
            allocation_status_choice = AllocationStatusChoice.objects.get(name="Active")
            for allocation_pk in project_review_obj.allocation_renewals.split(','):
                allocation = Allocation.objects.get(pk=int(allocation_pk))
                allocation.status = allocation_status_choice
                allocation.save()

        project_review_obj.save()
        project_obj.save()

        messages.success(request, 'Project review for {} has been DENIED'.format(
            project_review_obj.project.title)
        )

        if EMAIL_ENABLED:
            domain_url = get_domain_url(self.request)
            project_url = '{}{}'.format(domain_url, reverse(
                'project-detail', kwargs={'pk': project_review_obj.project.pk}
            ))
            not_renewed_allocation_urls = []
            if project_review_obj.allocation_renewals:
                for allocation_pk in project_review_obj.allocation_renewals.split(','):
                    allocation_url = '{}{}'.format(domain_url, reverse(
                        'allocation-detail', kwargs={'pk': allocation_pk}
                    ))
                    not_renewed_allocation_urls.append(allocation_url)

            template_context = {
                'project_title': project_review_obj.project.title,
                'project_url': project_url,
                'signature': EMAIL_SIGNATURE,
                'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                'center_name': EMAIL_CENTER_NAME,
                'not_renewed_allocation_urls': not_renewed_allocation_urls,
                'signature': EMAIL_SIGNATURE
            }

            email_receiver_list = get_project_user_emails(project_obj, True)
            send_email_template(
                'Your Project Renewal Was Denied',
                'email/project_renewal_denied.txt',
                template_context,
                EMAIL_TICKET_SYSTEM_ADDRESS,
                email_receiver_list
            )

        logger.info(
            f'Admin {request.user.username} denied a project renewal request (project pk={project_obj.pk})'
        )
        return HttpResponseRedirect(reverse('project-review-list'))


class ProjectReviewInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_review_info.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not self.request.user.is_superuser:
            if not self.request.user.has_perm('project.can_review_pending_projects'):
                return False

        project_review_obj = get_object_or_404(ProjectReview, pk=self.kwargs.get('pk'))
        if project_review_obj.status.name != 'Pending':
            messages.error(
                self.request, f'You cannot view a project review\'s info with status "{project_review_obj.status.name}"'
            )
            return False

        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        context['project_review'] = get_object_or_404(ProjectReview, pk=pk)

        return context


class ProjectReviewCompleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Currently not in use."""
    login_url = "/"

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_review_pending_projects'):
            return True

        messages.error(
            self.request, 'You do not have permission to mark a pending project review as completed.')

    def get(self, request, project_review_pk):
        project_review_obj = get_object_or_404(
            ProjectReview, pk=project_review_pk)

        project_review_status_completed_obj = ProjectReviewStatusChoice.objects.get(
            name='Completed')
        project_review_obj.status = project_review_status_completed_obj
        project_review_obj.project.project_needs_review = False
        project_review_obj.save()

        messages.success(request, 'Project review for {} has been completed'.format(
            project_review_obj.project.title)
        )

        return HttpResponseRedirect(reverse('project-review-list'))


class ProjectReivewEmailView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = ProjectReviewEmailForm
    template_name = 'project/project_review_email.html'
    login_url = "/"

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not EMAIL_ENABLED:
            messages.error(
                self.request, 'Emails are not enabled.')
            return False

        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_review_pending_projects'):
            return True

        messages.error(
            self.request, 'You do not have permission to send email for a pending project review.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        project_review_obj = get_object_or_404(ProjectReview, pk=pk)
        context['project_review'] = project_review_obj

        return context

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.kwargs.get('pk'), **self.get_form_kwargs())

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        project_review_obj = get_object_or_404(ProjectReview, pk=pk)
        form_data = form.cleaned_data

        if EMAIL_ENABLED:
            receiver_list = [project_review_obj.project.pi.email]
            cc = form_data.get('cc').strip()
            if cc:
                cc = cc.split(',')
            else:
                cc = []

            send_email(
                'Request for more information',
                form_data.get('email_body'),
                EMAIL_DIRECTOR_EMAIL_ADDRESS,
                receiver_list,
                cc
            )
            success_text = 'Email sent to {} {} ({}).'.format(
                project_review_obj.project.pi.first_name,
                project_review_obj.project.pi.last_name,
                project_review_obj.project.pi.username
            )
            if cc:
                success_text += ' CCed: {}'.format(', '.join(cc))

            messages.success(self.request, success_text)
        else:
            messages.error(self.request, 'Failed to send email: Email not enabled')

            logger.warning(
                'Email has not been enabled'
            )
            return super().form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-review-list')


class ProjectRequestEmailView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = ProjectRequestEmailForm
    template_name = 'project/project_request_email.html'
    login_url = "/"

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if not EMAIL_ENABLED:
            messages.error(
                self.request, 'Emails are not enabled.')
            return False

        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_review_pending_projects'):
            return True

        messages.error(
            self.request, 'You do not have permission to send email for a pending project request.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)
        context['project'] = project_obj

        return context

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.kwargs.get('pk'), **self.get_form_kwargs())

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)
        form_data = form.cleaned_data

        if EMAIL_ENABLED:
            receiver_list = [project_obj.pi.email]
            cc = form_data.get('cc').strip()
            if cc:
                cc = cc.split(',')
            else:
                cc = []

            send_email(
                'Request for more information',
                form_data.get('email_body'),
                EMAIL_DIRECTOR_EMAIL_ADDRESS,
                receiver_list,
                cc
            )

            success_text = 'Email sent to {} {} ({}).'.format(
                project_obj.pi.first_name,
                project_obj.pi.last_name,
                project_obj.pi.username
            )
            if cc:
                success_text += ' CCed: {}'.format(', '.join(cc))

            messages.success(self.request, success_text)
        else:
            messages.error(self.request, 'Failed to send email: Email not enabled')

            logger.warning(
                'Email has not been enabled'
            )
            return super().form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-review-list')


class ProjectRequestAccessEmailView(LoginRequiredMixin, View):

    def post(self, request):
        project_obj = get_object_or_404(Project, pk=request.POST.get('project_pk'))
        if project_obj.private is True:
            logger.warning(
                "User {} attempted to request access to a private project (pk={})".format(
                    request.user.username,
                    project_obj.pk
                )
            )
            return HttpResponseForbidden(reverse('project-list'))

        domain_url = get_domain_url(self.request)
        project_url = '{}{}'.format(domain_url, reverse('project-detail', kwargs={'pk': project_obj.pk}))

        if EMAIL_ENABLED:
            send_email_template(
                'Add User to Project Request',
                'email/project_add_user_request.txt',
                {
                    'user': request.user,
                    'project_title': project_obj.title,
                    'project_url': project_url,
                    'help_email': EMAIL_TICKET_SYSTEM_ADDRESS,
                    'signature': EMAIL_SIGNATURE
                },
                EMAIL_TICKET_SYSTEM_ADDRESS,
                [project_obj.pi.email]
            )
            logger.info(
                f'User {request.user.username} sent an email to {project_obj.pi.email} requesting '
                f'access to their project (project pk={project_obj.pk})'
            )
        else:
            logger.warning(
                'Email has not been enabled'
            )
            return HttpResponseForbidden(reverse('project-list'))

        return HttpResponseRedirect(reverse('project-list'))


class ProjectNoteCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProjectUserMessage
    fields = '__all__'
    template_name = 'project/project_note_create.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""

        if self.request.user.is_superuser:
            return True
        else:
            messages.error(
                self.request, 'You do not have permission to add project notes.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)
        context['project'] = project_obj
        return context

    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get('pk')
        project_obj = get_object_or_404(Project, pk=pk)
        author = self.request.user
        initial['project'] = project_obj
        initial['author'] = author
        return initial

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        form = super().get_form(form_class)
        form.fields['project'].widget = forms.HiddenInput()
        form.fields['author'].widget = forms.HiddenInput()
        form.order_fields([ 'project', 'author', 'message', 'is_private' ])
        return form

    def get_success_url(self):
        logger.info(
            f'Admin {self.request.user.username} created a project note (pk={self.kwargs.get("pk")})'
        )
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('pk')})


class ProjectExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        
        if user.has_perm('project.can_view_all_projects'):
            return True
        
        messages.error(self.request, 'You do not have permission to download projects')

    def post(self, request):
        file_name = request.POST.get('file_name')
        project_creation_range_start = request.POST.get('project_creation_range_start')
        project_creation_range_stop = request.POST.get('project_creation_range_stop')
        project_statuses = request.POST.get('project_statuses')

        initial_data = {
            'file_name': file_name,
            'project_creation_range_start': project_creation_range_start,
            'project_creation_range_stop': project_creation_range_stop,
            'project_statuses': project_statuses
        }

        form = ProjectExportForm(
            request.POST,
            initial=initial_data
        )

        if form.is_valid():
            data = form.cleaned_data
            file_name = data.get('file_name')
            project_creation_range_start = data.get('project_creation_range_start')
            project_creation_range_stop = data.get('project_creation_range_stop')
            project_statuses = data.get('project_statuses')

            if file_name[-4:] != ".csv":
                file_name += ".csv"

            if project_statuses:
                projects = Project.objects.filter(status__in=project_statuses).order_by("created")
            else:
                projects = Project.objects.all().order_by('created')

            if project_creation_range_start:
                projects = projects.filter(
                    created__gte=project_creation_range_start
                ).order_by('-created')

            if project_creation_range_stop:
                projects = projects.filter(
                    created__lte=project_creation_range_stop
                ).order_by('-created')

            rows = []
            header = [
                'Project ID',
                'Project Title',
                'Project Description',
                'Project Status',
                'Created On'
            ]

            for project in projects:
                row = [
                    project.pk,
                    project.title,
                    project.description,
                    project.status,
                    project.created
                ]

                rows.append(row)

            rows.insert(0, header)

            psuedo_buffer = Echo()
            writer = csv.writer(psuedo_buffer)
            response = StreamingHttpResponse(
                (writer.writerow(row) for row in rows),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}'

            logger.info(f'Admin {request.user.username} exported the project list')

            return response
        else:
            messages.error(
                request,
                'Please correct the errors for the following fields: {}'
                .format(' '.join(form.errors))
            )
            return HttpResponseRedirect(reverse('project-list'))


class ProjectUserExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """ UserPassesTestMixin Tests"""
        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('project.can_view_all_projects'):
            return True

        messages.error(self.request, 'You do not have permission to download project users.')

    def post(self, request):
        file_name = request.POST.get('file_name')
        project_creation_range_start = request.POST.get('project_creation_range_start')
        project_creation_range_stop = request.POST.get('project_creation_range_stop')
        project_statuses = request.POST.get('project_statuses')
        project_user_roles = request.POST.get('project_user_roles')

        initial_data = {
            'file_name': file_name,
            'project_creation_range_start': project_creation_range_start,
            'project_creation_range_stop': project_creation_range_stop,
            'project_statuses': project_statuses,
            'project_user_roles': project_user_roles
        }

        form = ProjectUserExportForm(
            request.POST,
            initial=initial_data
        )

        if form.is_valid():
            data = form.cleaned_data
            file_name = data.get('file_name')
            project_creation_range_start = data.get('project_creation_range_start')
            project_creation_range_stop = data.get('project_creation_range_stop')
            project_statuses = data.get('project_statuses')
            project_user_roles = data.get('project_user_roles')

            if file_name[-4:] != ".csv":
                file_name += ".csv"

            if project_statuses:
                projects = Project.objects.filter(status__in=project_statuses).order_by('created')
            else:
                projects = Project.objects.all().order_by('created')

            if project_creation_range_start:
                projects = projects.filter(
                    created__gte=project_creation_range_start
                ).order_by('-created')

            if project_creation_range_stop:
                projects = projects.filter(
                    created__lte=project_creation_range_stop
                ).order_by('-created')

            rows = []
            header = [
                'Project Title',
                'Project ID',
                'Project Status',
                'Slurm Account Name',
                'Creation Date',
                'Username',
                'Email',
                'Role'
            ]

            for project in projects:
                if project_user_roles:
                    project_users = project.projectuser_set.filter(role__in=project_user_roles).order_by('user__username')
                else:
                    project_users = project.projectuser_set.all().order_by('user__username')

                for project_user in project_users:
                    row = [
                        project.title,
                        project.pk,
                        project.status.name,
                        project.slurm_account_name,
                        project.created,
                        project_user.user.username,
                        project_user.user.email,
                        project_user.role.name
                    ]

                    rows.append(row)
            rows.insert(0, header)

            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse(
                (writer.writerow(row) for row in rows),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'

            logger.info(f'Admin {request.user.username} exported the project user list')

            return response
        else:
            messages.error(
                request,
                'Please correct the errors for the following fields: {}'
                .format(' '.join(form.errors))
            )
            return HttpResponseRedirect(reverse('project-list'))
