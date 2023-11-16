from django import forms
from django.template.loader import render_to_string

from crispy_forms.helper import FormHelper
from crispy_forms.layout import  Layout, Submit, HTML, Row, Column,  Reset, LayoutObject, Div
from crispy_forms.bootstrap import  FormActions,  AccordionGroup, Accordion, TabHolder, Tab

from coldfront.core.project.models import ProjectTypeChoice, ProjectStatusChoice
from coldfront.core.allocation.models import AllocationStatusChoice, AllocationAttributeType
from coldfront.core.resource.models import Resource, ResourceType


class AllocationAttributeFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_custom_control = False 
        self.layout = Layout(
            Div(
                Div(
                    Row(
                        Column('allocationattribute__name'),
                        Column('allocationattribute__value'),
                    ),
                    Row(
                        Column('allocationattribute__has_usage'),
                        Column('allocationattribute__equality'),
                        Column('allocationattribute__usage'),
                        Column('allocationattribute__usage_format')
                    ),
                    css_class='card-body'
                ),
                css_class='card mb-3'
            )
        )


class AllocationAttributeSearchForm(forms.Form):
    EQUALITY_CHOICES = (
        ('lt', '<'),
        ('gt', '>')
    )
    FORMAT_CHOICES = (
        ('whole', '.00'),
        ('percent', '%')
    )
    YES_NO_CHOICES = (
        (1, 'Yes'),
        (0, 'No')
    )

    allocationattribute__name = forms.ModelChoiceField(
        label='Allocation Attribute Name',
        queryset=AllocationAttributeType.objects.none() ,
        help_text=(
            f'To display the list of allocation attributes at least one resource must be selected.'
        ),
        required=False,
    )
    allocationattribute__value = forms.CharField(
        label='Allocation Attribute Value',
        max_length=50,
        required=False
    )
    allocationattribute__has_usage = forms.ChoiceField(
        initial=0, label='Has usage', choices=YES_NO_CHOICES, required=False,
    )
    allocationattribute__equality = forms.ChoiceField(
        label='Equality', choices=EQUALITY_CHOICES, required=False
    )
    allocationattribute__usage = forms.FloatField(label='Usage' , required=False)
    allocationattribute__usage_format = forms.ChoiceField(
        label='Format', choices=FORMAT_CHOICES, required=False
    )

    def __init__(self, *args, resources=None, **kwargs):
        super().__init__(*args, **kwargs)
        if resources:
            self.fields['allocationattribute__name'].queryset = AllocationAttributeType.objects.prefetch_related(
                'attribute_type'
            ).filter(linked_resources__in=resources).distinct().order_by('name')
        else:
            self.fields['allocationattribute__name'].queryset = AllocationAttributeType.objects.none() 


class SearchForm(forms.Form):
    only_search_projects = forms.BooleanField(
        required=False,
        help_text='Enables only filtering projects. Disables all other filters and selections.'
    )

    display__project__id = forms.BooleanField(required=False)

    project__title = forms.CharField(
        label='Project Title Contains', max_length=100, required=False
    )
    display__project__title = forms.BooleanField(required=False)

    project__description = forms.CharField(
        label='Project Description Contains', max_length=100, required=False
    )
    display__project__description = forms.BooleanField(required=False)

    project__pi__username = forms.CharField(
        label='PI Username Contains', max_length=25, required=False
    )
    display__project__pi__username = forms.BooleanField(required=False)

    project__requestor__username = forms.CharField(
        label='Requestor Username Contains', max_length=25, required=False
    )
    display__project__requestor__username = forms.BooleanField(required=False)

    project__user_username = forms.CharField(
        label='Username Contains', max_length=25, required=False, help_text='Active user'
    )

    project__status__name = forms.ModelMultipleChoiceField(
        label='Project Status',
        queryset=ProjectStatusChoice.objects.all().order_by('name'),
        required=False
    )
    display__project__status__name = forms.BooleanField(required=False)

    project__type__name = forms.ModelMultipleChoiceField(
        label='Project Type',
        queryset=ProjectTypeChoice.objects.all().order_by('name'),
        required=False
    )
    display__project__type__name = forms.BooleanField(required=False)

    project__class_number = forms.CharField(
        label='Class Number', max_length=25, required=False
    )
    display__project__class_number = forms.BooleanField(required=False)

    display__project__users = forms.BooleanField(
        required=False,
        help_text='Active users. Enable by selecting "only search projects". Enables the user profiles section.'
    )

    display__project__total_users = forms.BooleanField(required=False, help_text='Active users')

    display__allocation__id = forms.BooleanField(required=False)

    allocation__user_username = forms.CharField(
        label='Username Contains', max_length=25, required=False, help_text='Active user'
    )

    allocation__status__name = forms.ModelMultipleChoiceField(
        label='Allocation Status',
        queryset=AllocationStatusChoice.objects.all().order_by('name'),
        required=False
    )
    display__allocation__status__name = forms.BooleanField(required=False)

    display__allocation__users = forms.BooleanField(
        required=False, help_text='Active users. Enables the user profiles section.'
    )

    display__allocation__total_users = forms.BooleanField(required=False, help_text='Active users')

    resources__name = forms.ModelMultipleChoiceField(
        label='Resource Name',
        queryset=Resource.objects.filter(is_allocatable=True).order_by('name'),
        required=False
    )
    display__resources__name = forms.BooleanField(required=False)

    resources__resource_type__name = forms.ModelMultipleChoiceField(
        label='Resource Type',
        queryset=ResourceType.objects.all().order_by('name'),
        required=False
    )
    display__resources__resource_type__name = forms.BooleanField(required=False)

    allocationattribute_form = AllocationAttributeSearchForm()
    allocationattribute_helper = AllocationAttributeFormSetHelper()

    user__userprofile__department = forms.CharField(label="Department Contains", max_length=100, required=False)
    display__user__userprofile__department = forms.BooleanField(label='Display user department', required=False)

    user__userprofile__title = forms.CharField(label="Title Contains", max_length=30, required=False)
    display__user__userprofile__title = forms.BooleanField(label='Display user title', required=False)

    current_tab = forms.IntegerField(initial=1, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.use_custom_control = False 
        self.helper.layout = Layout(
            TabHolder(
                Tab('Allocation & Project Search',
                    Accordion(
                        AccordionGroup('Projects',
                            'only_search_projects',
                            Accordion(
                                AccordionGroup(
                                    'Filters',
                                    'project__title',
                                    'project__description',
                                    'project__pi__username',
                                    'project__requestor__username',
                                    'project__user_username',
                                    'project__status__name',
                                    'project__type__name',
                                    'project__class_number',
                                    active=False,
                                ),
                            ),
                            Accordion(
                                AccordionGroup(
                                    'Displays',
                                    'display__project__id',
                                    'display__project__title',
                                    'display__project__description',
                                    'display__project__pi__username',
                                    'display__project__requestor__username',
                                    'display__project__status__name',
                                    'display__project__type__name',
                                    'display__project__class_number',
                                    'display__project__users',
                                    'display__project__total_users',
                                    active=False,
                                ),
                            ),
                            active=False,
                        ),
                    ),
                    Accordion(
                        AccordionGroup('Allocations',
                            'allocation__user_username',
                            'allocation__status__name',
                            'display__allocation__id',
                            'display__allocation__status__name',
                            'display__allocation__users',
                            'display__allocation__total_users',
                            active=False,
                        )
                    ),
                    Accordion(
                        AccordionGroup('Resources',
                            'resources__name',
                            'resources__resource_type__name',
                            'display__resources__name',
                            'display__resources__resource_type__name',
                            active=False,
                        )
                    ),
                    Accordion(
                        AccordionGroup('Allocation Attributes',
                            Formset('allocationattribute_form', 'allocationattribute_helper', label='allocationattribute_formset'),
                            HTML(
                                '<button id="id_formset_add_allocation_attribute_button" type="button" class="btn btn-primary">Add Allocation Attribute</button>'
                            ),
                            active=False,
                        )
                    ),
                    css_id='allocation-project-search'
                ),
                Tab('User Search',
                    Accordion(
                        AccordionGroup('User Profiles',
                            'enable_user_search',                               
                            'user__userprofile__department',
                            'user__userprofile__title',
                            'display__user__userprofile__department',
                            'display__user__userprofile__title',
                            active=False,
                        ),
                    ),
                    css_id='user-search'
                )
            ),
        
            FormActions(
                Submit('submit', 'Search'),
                Reset('reset', 'Reset')
            ),
            'current_tab'
        )

class Formset(LayoutObject):
    template = "advanced_search/formset.html"

    def __init__(self, formset_context_name, helper_context_name=None,
                 template=None, label=None):

        self.formset_context_name = formset_context_name
        self.helper_context_name = helper_context_name
        self.label = label

        # crispy_forms/layout.py:302 requires us to have a fields property
        self.fields = []

        # Overrides class variable with an instance level variable
        if template:
            self.template = template

    def render(self, form, form_style, context, **kwargs):
        formset = context.get(self.formset_context_name)
        helper = context.get(self.helper_context_name)
        # closes form prematurely if this isn't explicitly stated
        if helper:
            helper.form_tag = False

        context.update({'formset': formset, 'helper': helper, 'label': self.label})
        return render_to_string(self.template, context.flatten())
