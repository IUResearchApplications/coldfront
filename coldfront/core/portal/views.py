import operator
from collections import Counter

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from coldfront.core.allocation.models import Allocation, AllocationUser
from coldfront.core.grant.models import Grant
from coldfront.core.portal.utils import (generate_allocations_chart_data,
                                         generate_publication_by_year_chart_data,
                                         generate_resources_chart_data,
                                         generate_total_grants_by_agency_chart_data,
                                         generate_project_type_chart_data,
                                         generate_project_user_chart_data,
                                         generate_user_counts,
                                         generate_user_timeline)
from coldfront.core.project.models import Project
from coldfront.core.publication.models import Publication
from coldfront.core.research_output.models import ResearchOutput
from coldfront.core.utils.common import import_from_settings

PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING = import_from_settings(
    'PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING',
    30
)
ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING = import_from_settings(
    'ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING',
    30
)
ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING = import_from_settings(
    'ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING',
    60
)


def home(request):

    context = {}
    next_url = ""
    if request.user.is_authenticated:
        template_name = 'portal/authorized_home.html'
        project_list = Project.objects.filter(
            (
                Q(pi=request.user) &
                Q(
                    status__name__in=[
                        'New',
                        'Active',
                        'Waiting For Admin Approval',
                        'Contacted By Admin',
                        'Review Pending',
                        'Expired'
                    ]
                )
            ) |
            (Q(
                status__name__in=[
                    'New',
                    'Active',
                    'Waiting For Admin Approval',
                    'Contacted By Admin',
                    'Review Pending'
                    ]
             ) &
             Q(projectuser__user=request.user) &
             Q(projectuser__status__name__in=['Active', ]))
        ).distinct().order_by('-created')[:5]

        allocation_list = Allocation.objects.filter(
            Q(status__name__in=['Active', 'New', 'Renewal Requested', 'Billing Information Submitted']) &
            Q(project__status__name__in=['Active', 'New', 'Review Pending', 'Expired']) &
            Q(project__projectuser__user=request.user) &
            Q(project__projectuser__status__name__in=['Active', ]) &
            Q(allocationuser__user=request.user) &
            Q(allocationuser__status__name__in=['Active', 'Pending - Remove', 'Invited', 'Pending', 'Disabled', 'Retired'])
        ).distinct().order_by('-created')

        allocation_list = allocation_list[:5]

        projects_with_a_slurm_account_to_list = []
        for project in project_list:
            resources_with_slurm_accounts = project.get_list_of_resources_with_slurm_accounts(request.user)
            if resources_with_slurm_accounts:
                project_dict = {
                    'title': project.title,
                    'slurm_account_name': project.slurm_account_name,
                    'resources_with_slurm_accounts': ', '.join(resources_with_slurm_accounts)
                }
                projects_with_a_slurm_account_to_list.append(project_dict)
        context['projects_with_a_slurm_account_to_list'] = projects_with_a_slurm_account_to_list

        context['user'] = request.user
        context['project_list'] = project_list
        context['allocation_list'] = allocation_list
        context['PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING'] = PROJECT_DAYS_TO_REVIEW_AFTER_EXPIRING
        context['ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING'] = ALLOCATION_DAYS_TO_REVIEW_BEFORE_EXPIRING
        context['ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING'] = ALLOCATION_DAYS_TO_REVIEW_AFTER_EXPIRING
        try:
            context['ondemand_url'] = settings.ONDEMAND_URL
        except AttributeError:
            pass
    else:
        next_url = request.get_full_path()[1:]
        template_name = 'portal/nonauthorized_home.html'
    context['next'] = next_url
    context['EXTRA_APPS'] = settings.INSTALLED_APPS

    if 'coldfront.plugins.system_monitor' in settings.INSTALLED_APPS:
        from coldfront.plugins.system_monitor.utils import get_system_monitor_context
        context.update(get_system_monitor_context())

    return render(request, template_name, context)


def center_summary(request):
    context = {}

    # Publications Card
    publications_by_year = list(Publication.objects.filter(year__gte=1999).values(
        'unique_id', 'year').distinct().values('year').annotate(num_pub=Count('year')).order_by('-year'))

    publications_by_year = [(ele['year'], ele['num_pub'])
                            for ele in publications_by_year]

    publication_by_year_bar_chart_data = generate_publication_by_year_chart_data(
        publications_by_year)
    context['publication_by_year_bar_chart_data'] = publication_by_year_bar_chart_data
    context['total_publications_count'] = Publication.objects.filter(
        year__gte=1999).values('unique_id', 'year').distinct().count()

    # Research Outputs card
    context['total_research_outputs_count'] = ResearchOutput.objects.all().distinct().count()

    # Grants Card
    total_grants_by_agency_sum = list(Grant.objects.values(
        'funding_agency__name').annotate(total_amount=Sum('total_amount_awarded')))

    total_grants_by_agency_count = list(Grant.objects.values(
        'funding_agency__name').annotate(count=Count('total_amount_awarded')))

    total_grants_by_agency_count = {
        ele['funding_agency__name']: ele['count'] for ele in total_grants_by_agency_count}

    total_grants_by_agency = [['{}: ${} ({})'.format(
        ele['funding_agency__name'],
        intcomma(int(ele['total_amount'])),
        total_grants_by_agency_count[ele['funding_agency__name']]
    ), ele['total_amount']] for ele in total_grants_by_agency_sum]

    total_grants_by_agency = sorted(
        total_grants_by_agency, key=operator.itemgetter(1), reverse=True)
    grants_agency_chart_data = generate_total_grants_by_agency_chart_data(
        total_grants_by_agency)
    context['grants_agency_chart_data'] = grants_agency_chart_data
    context['grants_total'] = intcomma(
        int(sum(list(Grant.objects.values_list('total_amount_awarded', flat=True)))))
    context['grants_total_pi_only'] = intcomma(
        int(sum(list(Grant.objects.filter(role='PI').values_list('total_amount_awarded', flat=True)))))
    context['grants_total_copi_only'] = intcomma(
        int(sum(list(Grant.objects.filter(role='CoPI').values_list('total_amount_awarded', flat=True)))))
    context['grants_total_sp_only'] = intcomma(
        int(sum(list(Grant.objects.filter(role='SP').values_list('total_amount_awarded', flat=True)))))

    return render(request, 'portal/center_summary.html', context)


@cache_page(60 * 15)
def allocation_by_fos(request):

    allocations_by_fos = Counter(list(Allocation.objects.filter(
        status__name='Active').values_list('project__field_of_science__description', flat=True)))

    user_allocations = AllocationUser.objects.filter(
        status__name__in=['Active', 'Invited', 'Pending', 'Disabled', 'Retired'], allocation__status__name='Active')

    active_users_by_fos = Counter(list(user_allocations.values_list(
        'allocation__project__field_of_science__description', flat=True)))
    total_allocations_users = user_allocations.values(
        'user').distinct().count()

    active_pi_count = Project.objects.filter(status__name__in=['Active', 'New']).values_list(
        'pi__username', flat=True).distinct().count()
    context = {}
    context['allocations_by_fos'] = dict(allocations_by_fos)
    context['active_users_by_fos'] = dict(active_users_by_fos)
    context['total_allocations_users'] = total_allocations_users
    context['active_pi_count'] = active_pi_count
    return render(request, 'portal/allocation_by_fos.html', context)


@cache_page(60 * 15)
def allocation_summary(request):

    allocation_resources = [
        allocation.get_parent_resource.parent_resource if allocation.get_parent_resource.parent_resource else allocation.get_parent_resource for allocation in Allocation.objects.filter(status__name='Active')]

    allocations_count_by_resource = dict(Counter(allocation_resources))

    allocation_count_by_resource_type = dict(
        Counter([ele.resource_type.name for ele in allocation_resources]))

    allocations_chart_data = generate_allocations_chart_data()
    resources_chart_data = generate_resources_chart_data(
        allocation_count_by_resource_type)

    context = {}
    context['allocations_chart_data'] = allocations_chart_data
    context['allocations_count_by_resource'] = allocations_count_by_resource
    context['resources_chart_data'] = resources_chart_data

    return render(request, 'portal/allocation_summary.html', context)


@cache_page(60 * 15)
def project_summary(request):
    context = {}
    context['project_user_chart_data'] = generate_project_user_chart_data()
    context['project_type_chart_data'] = generate_project_type_chart_data()

    return render(request, 'portal/project_summary.html', context)


@cache_page(60 * 15)
def user_summary(request):
    context = {}
    context['user_counts'] = generate_user_counts()
    user_timeline_chart_data, years_to_months_labels, years_to_months_values = generate_user_timeline()
    context['user_timeline'] = user_timeline_chart_data
    context['years_to_months_labels'] = years_to_months_labels
    context['years_to_months_values'] = years_to_months_values

    return render(request, 'portal/user_summary.html', context)
