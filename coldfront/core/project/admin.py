import textwrap

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from coldfront.core.project.models import (Project, ProjectAdminComment,
                                           ProjectReview, ProjectStatusChoice,
                                           ProjectUser, ProjectUserMessage,
                                           ProjectUserRoleChoice,
                                           ProjectUserStatusChoice,
                                           ProjectTypeChoice,
                                           ProjectReviewStatusChoice,
                                           ProjectAdminAction,
                                           ProjectDescriptionRecord)


@admin.register(ProjectStatusChoice)
class ProjectStatusChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUserRoleChoice)
class ProjectUserRoleChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUserStatusChoice)
class ProjectUserStatusChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUser)
class ProjectUserAdmin(SimpleHistoryAdmin):
    fields_change = ('user', 'project', 'role', 'enable_notifications', 'status', 'created', 'modified', )
    readonly_fields_change = ('user', 'project', 'created', 'modified', )
    list_display = ('pk', 'project_title', 'PI', 'User', 'role', 'status',
                    'created', 'modified',)
    list_filter = ('role', 'status')
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ('user', 'project')

    def project_title(self, obj):
        return textwrap.shorten(obj.project.title, width=50)

    def PI(self, obj):
        return '{} {} ({})'.format(obj.project.pi.first_name, obj.project.pi.last_name, obj.project.pi.username)

    def User(self, obj):
        return '{} {} ({})'.format(obj.user.first_name, obj.user.last_name, obj.user.username)

    def get_fields(self, request, obj):
        if obj is None:
            return super().get_fields(request)
        else:
            return self.fields_change

    def get_readonly_fields(self, request, obj):
        if obj is None:
            # We are adding an object
            return super().get_readonly_fields(request)
        else:
            return self.readonly_fields_change

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # We are adding an object
            return super().get_inline_instances(request)
        else:
            return [inline(self.model, self.admin_site) for inline in self.inlines]


class ProjectUserInline(admin.TabularInline):
    model = ProjectUser
    fields = ['user', 'project', 'role', 'status', 'enable_notifications', ]
    readonly_fields = ['user', 'project', ]
    extra = 0


class ProjectAdminCommentInline(admin.TabularInline):
    model = ProjectAdminComment
    extra = 0
    fields = ('comment', 'author', 'created'),
    readonly_fields = ('author', 'created')


class ProjectUserMessageInline(admin.TabularInline):
    model = ProjectUserMessage
    extra = 0
    fields = ('message', 'author', 'created'),
    readonly_fields = ('author', 'created')


class ProjectReviewInline(admin.TabularInline):
    model = ProjectReview
    fields = ['status', 'project_updates', 'allocation_renewals', 'created', ]
    readonly_fields = ['status', 'project_updates', 'allocation_renewals', 'created', ]
    extra = 0


class ProjectAdminActionInline(admin.TabularInline):
    model = ProjectAdminAction
    fields = ['user', 'action', 'created', ]
    readonly_fields = ['user', 'action', 'created']
    can_delete = False
    extra = 0


@admin.register(Project)
class ProjectAdmin(SimpleHistoryAdmin):
    fields_change = ('title', 'pi', 'requestor', 'description', 'slurm_account_name', 'private', 'type', 'class_number', 
                     'status', 'requires_review', 'force_review', 'max_managers', 'created', 'end_date', 'modified', )
    readonly_fields_change = ('created', 'modified', )
    list_display = ('pk', 'title', 'PI', 'created', 'modified', 'end_date', 'type', 'status')
    search_fields = ['pi__username', 'projectuser__user__username',
                     'projectuser__user__last_name', 'projectuser__user__last_name', 'title']
    list_filter = ('status', 'force_review', 'type')
    inlines = [ProjectUserInline, ProjectReviewInline, ProjectAdminCommentInline,
               ProjectUserMessageInline, ProjectAdminActionInline]
    raw_id_fields = ['pi', 'requestor', ]

    def PI(self, obj):
        return '{} {} ({})'.format(obj.pi.first_name, obj.pi.last_name, obj.pi.username)

    def get_fields(self, request, obj):
        if obj is None:
            return super().get_fields(request)
        else:
            return self.fields_change

    def get_readonly_fields(self, request, obj):
        if obj is None:
            # We are adding an object
            return super().get_readonly_fields(request)
        else:
            return self.readonly_fields_change

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # We are adding an object
            return []
        else:
            return super().get_inline_instances(request)

    def save_formset(self, request, form, formset, change):
        if formset.model in [ProjectAdminComment, ProjectUserMessage]:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.author = request.user
                instance.save()
        else:
            formset.save()


@admin.register(ProjectReview)
class ProjectReviewAdmin(SimpleHistoryAdmin):
    list_display = ('pk', 'project', 'PI', 'allocation_renewals', 'project_updates', 'created', 'status')
    search_fields = ['project__pi__username', 'project__pi__first_name', 'project__pi__last_name',]
    list_filter = ('status', )

    def PI(self, obj):
        return '{} {} ({})'.format(obj.project.pi.first_name, obj.project.pi.last_name, obj.project.pi.username)


@admin.register(ProjectTypeChoice)
class ProjectTypeChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectReviewStatusChoice)
class ProjectReviewStatusChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectAdminAction)
class ProjectAdminActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'project_pk', 'project_title', 'action', 'created', )
    readonly_fields = ('user', 'project_pk', 'project', 'action', 'created', )
    list_filter = ('action', )

    def project_pk(self, obj):
        return obj.project.pk

    def project_title(self, obj):
        return obj.project.title


@admin.register(ProjectDescriptionRecord)
class ProjectDescriptionRecordAdmin(admin.ModelAdmin):
    list_display = ('pk', 'project', 'user', 'created')
    readonly_fields = ('project', 'user', 'description')
    list_filter = ('project', )