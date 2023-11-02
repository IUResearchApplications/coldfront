import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.expressions import ExpressionWrapper, F, Q
from django.db.models import BooleanField, Prefetch
from django.views import View
from django.db.models.functions import Lower
from django.contrib.auth.models import User

from coldfront.core.project.models import ProjectUser, ProjectUserRoleChoice
from coldfront.core.resource.models import ResourceType

class UserReportPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        
    def create_paragraph(self, story, label, text, style):
        story.append(
            Paragraph(f'<strong>{label}:</strong> {text}', style)
        )
        story.append(Spacer(1, 2))
        return story
    
    def get_full_name(self, user_obj):
        full_name = f'{user_obj.first_name} {user_obj.last_name}'
        if not full_name:
            return user_obj.username
        return full_name
    
    def get_project_users_by_role(self, project_user_objs):
        project_users = {}
        project_user_role_choice_objs = ProjectUserRoleChoice.objects.all()
        for project_user_role_choice_obj in project_user_role_choice_objs:
            project_users_by_role = project_user_objs.filter(role=project_user_role_choice_obj)
            if not project_users_by_role.exists():
                project_users[project_user_role_choice_obj.name] = ['None']
            else:
                full_names = [
                    self.get_full_name(project_user_by_role.user)
                    for project_user_by_role in project_users_by_role
                ]
                project_users[project_user_role_choice_obj.name] = full_names

        return project_users

    def get_project_allocations_by_type(self, allocation_objs):
        allocations = {}
        resource_type_objs = ResourceType.objects.all()
        for resource_type_obj in resource_type_objs:
            allocations_by_type = allocation_objs.filter(
                resources__resource_type=resource_type_obj
            ).values_list('resources__name', flat=True)
            if allocations_by_type.exists():
                allocations[resource_type_obj.name] = allocations_by_type

        return allocations


    def get(self, request):
        username = request.GET.get('user')
        viewed_user = User.objects.get(username=username)
        ongoing_projectuser_statuses = (
            'Active',
            'Pending - Add',
            'Pending - Remove',
        )
        ongoing_project_statuses = (
            'New',
            'Active',
            'Review Pending'
        )

        qs = ProjectUser.objects.filter(
            user=viewed_user,
            status__name__in=ongoing_projectuser_statuses,
            project__status__name__in=ongoing_project_statuses,
        ).select_related(
            'status',
            'role',
            'project',
            'project__status',
            'project__field_of_science',
            'project__pi',
        ).only(
            'status__name',
            'role__name',
            'project__title',
            'project__status__name',
            'project__field_of_science__description',
            'project__pi__username',
            'project__pi__first_name',
            'project__pi__last_name',
            'project__pi__email',
        ).annotate(
            is_project_pi=ExpressionWrapper(
                Q(user=F('project__pi')),
                output_field=BooleanField(),
            ),
            is_project_manager=ExpressionWrapper(
                Q(role__name='Manager'),
                output_field=BooleanField(),
            ),
        ).order_by(
            '-is_project_pi',
            '-is_project_manager',
            Lower('project__pi__username').asc(),
            Lower('project__title').asc(),
            # unlikely things will get to this point unless there's almost-duplicate projects
            '-project__pk',  # more performant stand-in for '-project__created'
        ).prefetch_related(
            Prefetch(
                lookup='project__projectuser_set',
                queryset=ProjectUser.objects.filter(
                    role__name='Manager',
                    status__name__in=ongoing_projectuser_statuses,
                ).exclude(
                    user__pk__in=[
                        F('project__pi__pk'),  # we assume pi is 'Manager' or can act like one - no need to list twice
                        viewed_user.pk,  # we display elsewhere if the user is a manager of this project
                    ],
                ).select_related(
                    'status',
                    'user',
                ).only(
                    'status__name',
                    'user__username',
                    'user__first_name',
                    'user__last_name',
                    'user__email',
                ).order_by(
                    'user__username',
                ),
                to_attr='project_managers',
            ),
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            title=f'User Report - {viewed_user.first_name} {viewed_user.last_name}',
            displayDocTitle=True,
            pagesize=letter
        )
        styles = getSampleStyleSheet()
        style_normal = styles.get('Normal')
        style_title = styles.get('Title')
        style_heading1 = styles.get('Heading1')
        style_heading2 = styles.get('Heading2')

        story = []

        pdf_title = Paragraph(f'User Report - {viewed_user.first_name} {viewed_user.last_name}', style_title)
        story.append(pdf_title)
        story.append(Spacer(1, 2))
        for project_user_obj in qs:
            project_obj = project_user_obj.project
            story.append(HRFlowable(width='100%', spaceBefore=5, spaceAfter=5))
            project_title = Paragraph(f'Project: {project_obj.title}', style_heading1)
            story.append(project_title)

            project_information = Paragraph(f'Project Information', style_heading2)
            story.append(project_information)
            story.append(HRFlowable(width='50%', spaceBefore=5, spaceAfter=5, hAlign='LEFT'))
            story = self.create_paragraph(story, 'Status', project_obj.status.name, style_normal)
            story = self.create_paragraph(story, 'Description', project_obj.description, style_normal)
            project_pi = f'{project_obj.pi.first_name} {project_obj.pi.last_name}'
            story = self.create_paragraph(story, 'PI', project_pi, style_normal)
            project_requestor = f'{project_obj.requestor.first_name} {project_obj.requestor.last_name}'
            if project_pi != project_requestor:
                story = self.create_paragraph(story, 'Requestor', project_requestor, style_normal)
            story = self.create_paragraph(story, 'Created', project_obj.created.date(), style_normal)

            project_user_roles = Paragraph(f'Project User Roles', style_heading2)
            story.append(project_user_roles)
            story.append(HRFlowable(width='50%', spaceBefore=5, spaceAfter=5, hAlign='LEFT'))
            project_user_objs = project_obj.projectuser_set.filter(status__name="Active")
            for role, project_users in self.get_project_users_by_role(project_user_objs).items():
                story = self.create_paragraph(
                    story, role + 's', ', '.join(project_users), style_normal
                )

            project_allocations = Paragraph(f'Project Allocations', style_heading2)
            story.append(project_allocations)
            story.append(HRFlowable(width='50%', spaceBefore=5, spaceAfter=5, hAlign='LEFT'))
            allocation_objs =  project_obj.allocation_set.filter(status__name__in=["Active", "Renewal Requested"])
            allocation_objs_by_type = self.get_project_allocations_by_type(allocation_objs).items()
            if allocation_objs_by_type:
                for type, allocations in allocation_objs_by_type:
                    story = self.create_paragraph(
                        story, type,', '.join(allocations), style_normal 
                    )
            else:
                story.append(Paragraph('None', style_normal))

        doc.build(story)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="user_report.pdf")