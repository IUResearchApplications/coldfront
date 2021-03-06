from datetime import date
from coldfront.core.user.models import UserProfile
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.html import format_html

from coldfront.core.allocation.models import (AllocationAccount,
                                              AllocationAttributeType,
                                              AllocationAttribute,
                                              AllocationStatusChoice)
from coldfront.core.allocation.utils import get_user_resources
from coldfront.core.project.models import Project
from coldfront.core.resource.models import Resource, ResourceType
from coldfront.core.utils.common import import_from_settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit, HTML
from crispy_forms.bootstrap import InlineRadios, FormActions, PrependedText


ALLOCATION_ACCOUNT_ENABLED = import_from_settings(
    'ALLOCATION_ACCOUNT_ENABLED', False)
ALLOCATION_CHANGE_REQUEST_EXTENSION_DAYS = import_from_settings(
    'ALLOCATION_CHANGE_REQUEST_EXTENSION_DAYS', [])


class AllocationForm(forms.Form):
    YES_NO_CHOICES = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    # Leave an empty value as a choice so the form picks it as the value to check if the user has
    # already picked a choice (relevent if the form errors after submission due to missing required
    # values, prevents what the user chose from being reset. We want to check against an empty
    # string).
    CAMPUS_CHOICES = (
        ('', ''),
        ('BL', 'IU Bloomington'),
        ('IN', 'IUPUI (Indianapolis)'),
        ('CO', 'IUPUC (Columbus)'),
        ('EA', 'IU East (Richmond)'),
        ('FW', 'IU Fort Wayne'),
        ('CO', 'IU Kokomo'),
        ('NW', 'IU Northwest (Gary)'),
        ('SB', 'IU South Bend'),
        ('SE', 'IU Southeast (New Albany)'),
        ('OR', 'Other')
    )
    TRAINING_INFERENCE_CHOICES = (
        ('', ''),
        ('Training', 'Training'),
        ('Inference', 'Inference'),
        ('Both', 'Both')
    )
    GRAND_CHALLENGE_CHOICES = (
        ('', ''),
        ('healthinitiative', 'Precision Health Initiative'),
        ('envchange', 'Prepared for Environmental Change'),
        ('addiction', 'Responding to the Addiction Crisis')
    )
    STORAGE_UNIT_CHOICES = (
        ('GB', 'GB'),
        ('TB', 'TB')
    )
    SYSTEM_CHOICES = (
        ('Carbonate', 'Carbonate'),
        ('BigRed3', 'Big Red 3')
    )
    ACCESS_LEVEL_CHOICES = (
        ('Masked', 'Masked'),
        ('Unmasked', 'Unmasked')
    )
    LICENSE_TERM_CHOICES = (
        ('current', 'Current license'),
        ('current_and_next_year', 'Current license + next annual license')
    )

    resource = forms.ModelChoiceField(queryset=None, empty_label=None)
    justification = forms.CharField(widget=forms.Textarea)
    first_name = forms.CharField(max_length=40, required=False)
    last_name = forms.CharField(max_length=40, required=False)
    campus_affiliation = forms.ChoiceField(choices=CAMPUS_CHOICES, required=False)
    email = forms.EmailField(max_length=40, required=False)
    url = forms.CharField(max_length=50, required=False)
    project_directory_name = forms.CharField(max_length=10, required=False)
    quantity = forms.IntegerField(required=False)
    storage_space = forms.IntegerField(required=False)
    storage_space_unit = forms.ChoiceField(choices=STORAGE_UNIT_CHOICES, required=False, widget=RadioSelect)
    leverage_multiple_gpus = forms.ChoiceField(choices=YES_NO_CHOICES, required=False, widget=RadioSelect)
    dl_workflow = forms.ChoiceField(choices=YES_NO_CHOICES, required=False, widget=RadioSelect)
    applications_list = forms.CharField(max_length=150, required=False)
    training_or_inference = forms.ChoiceField(choices=TRAINING_INFERENCE_CHOICES, required=False)
    for_coursework = forms.ChoiceField(choices=YES_NO_CHOICES, required=False, widget=RadioSelect)
    system = forms.ChoiceField(choices=SYSTEM_CHOICES, required=False, widget=RadioSelect)
    is_grand_challenge = forms.BooleanField(required=False)
    grand_challenge_program = forms.ChoiceField(choices=GRAND_CHALLENGE_CHOICES, required=False)
    start_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}), required=False)
    end_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}), required=False)
    use_indefinitely = forms.BooleanField(required=False)
    phi_association = forms.ChoiceField(choices=YES_NO_CHOICES, required=False, widget=RadioSelect)
    access_level = forms.ChoiceField(choices=ACCESS_LEVEL_CHOICES, required=False, widget=RadioSelect)
    primary_contact = forms.CharField(max_length=20, required=False)
    secondary_contact = forms.CharField(max_length=20, required=False)
    department_full_name = forms.CharField(max_length=30, required=False)
    department_short_name = forms.CharField(max_length=15, required=False)
    fiscal_officer = forms.CharField(max_length=20, required=False)
    account_number = forms.CharField(max_length=9, required=False)
    sub_account_number = forms.CharField(max_length=20, required=False)
    license_term = forms.ChoiceField(choices=LICENSE_TERM_CHOICES, required=False)
    faculty_email = forms.EmailField(max_length=40, required=False)
    store_ephi = forms.ChoiceField(choices=YES_NO_CHOICES, required=False, widget=RadioSelect)
    it_pros = forms.CharField(max_length=100, required=False)
    devices_ip_addresses = forms.CharField(max_length=200, required=False)
    data_management_plan = forms.CharField(widget=forms.Textarea, required=False)
    prorated_cost = forms.IntegerField(disabled=True, required=False)
    cost = forms.IntegerField(disabled=True, required=False)
    total_cost = forms.IntegerField(disabled=True, required=False)
    confirm_understanding = forms.BooleanField(required=False)
    data_manager = forms.CharField(max_length=50, required=False)

    users = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, required=False)
    allocation_account = forms.ChoiceField(required=False)

    def __init__(self, request_user, project_pk,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        project_obj = get_object_or_404(Project, pk=project_pk)
        self.project_obj = project_obj
        self.request_user = request_user
        self.fields['resource'].queryset = get_user_resources(request_user)
        user_query_set = project_obj.projectuser_set.select_related('user').filter(
            status__name__in=['Active', ]).order_by("user__username")
        user_query_set = user_query_set.exclude(user__in=[project_obj.pi, request_user])

        if user_query_set:
            self.fields['users'].choices = ((user.user.username, "%s %s (%s)" % (
                user.user.first_name, user.user.last_name, user.user.username)) for user in user_query_set)
            self.fields['users'].help_text = '<br/>Select users in your project to add to this allocation.'
        else:
            self.fields['users'].widget = forms.HiddenInput()

        if ALLOCATION_ACCOUNT_ENABLED:
            allocation_accounts = AllocationAccount.objects.filter(
                user=request_user)
            if allocation_accounts:
                self.fields['allocation_account'].choices = (((account.name, account.name))
                                                             for account in allocation_accounts)

            self.fields['allocation_account'].help_text = '<br/>Select account name to associate with resource. <a href="#Modal" id="modal_link">Click here to create an account name!</a>'
        else:
            self.fields['allocation_account'].widget = forms.HiddenInput()

        self.fields['justification'].help_text = '<br/>Justification for requesting this allocation.'
        self.fields['start_date'].help_text = 'Format: mm/dd/yyyy'
        self.fields['end_date'].help_text = 'Format: mm/dd/yyyy'
        self.fields['account_number'].help_text = 'Format: 00-000-00'
        self.fields['applications_list'].help_text = 'Format: app1,app2,app3,etc'
        self.fields['it_pros'].help_text = 'Format: name1,name2,name3,etc'
        self.fields['project_directory_name'].help_text = 'Must be alphanumeric and not exceed 10 characters in length'
        self.fields['data_manager'].help_text = 'Must be a project Manager. Only this user can add and remove users from this resource. They will automatically be added to the resource.'

        user_profile = UserProfile.objects.get(user=request_user)
        self.fields['department_full_name'].initial = user_profile.department
        self.fields['first_name'].initial = user_profile.user.first_name
        self.fields['last_name'].initial = user_profile.user.last_name

        if 'coldfront.plugins.ldap_user_info' in settings.INSTALLED_APPS:
            from coldfront.plugins.ldap_user_info.utils import get_user_info
            attributes = get_user_info(request_user.username, ['division', 'ou', 'mail'])
            self.fields['department_short_name'].initial = attributes['division'][0]
            self.fields['campus_affiliation'].initial = attributes['ou'][0]
            self.fields['email'].initial = attributes['mail'][0]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'resource',
            'justification',
            'first_name',
            'last_name',
            'campus_affiliation',
            'email',
            'url',
            'project_directory_name',
            'quantity',
            'storage_space',
            InlineRadios('storage_space_unit'),
            InlineRadios('leverage_multiple_gpus'),
            InlineRadios('dl_workflow'),
            'applications_list',
            'training_or_inference',
            InlineRadios('for_coursework'),
            InlineRadios('system'),
            'is_grand_challenge',
            'grand_challenge_program',
            'start_date',
            'end_date',
            'use_indefinitely',
            InlineRadios('phi_association'),
            InlineRadios('access_level'),
            'primary_contact',
            'secondary_contact',
            'data_manager',
            'department_full_name',
            'department_short_name',
            'fiscal_officer',
            Field('account_number', placeholder='00-000-00'),
            'sub_account_number',
            'license_term',
            'faculty_email',
            InlineRadios('store_ephi'),
            'it_pros',
            'devices_ip_addresses',
            'data_management_plan',
            PrependedText('prorated_cost', '$'),
            PrependedText('cost', '$'),
            PrependedText('total_cost', '$'),
            'confirm_understanding',
            'users',
            'allocation_account',
            FormActions(
                Submit('submit', 'Submit'),
                HTML("""<a class="btn btn-secondary" href="{% url 'project-detail' project.pk %}"
                     role="button">Back to Project</a><br>"""),
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        resource_obj = cleaned_data.get('resource')
        users = cleaned_data.get('users')
        resources = {
            'Carbonate DL': {
                'leverage_multiple_gpus': cleaned_data.get('leverage_multiple_gpus'),
                'training_or_inference': cleaned_data.get('training_or_inference'),
                'for_coursework': cleaned_data.get('for_coursework'),
            },
            'Carbonate GPU': {
                'leverage_multiple_gpus': cleaned_data.get('leverage_multiple_gpus'),
                'dl_workflow': cleaned_data.get('dl_workflow'),
                'for_coursework': cleaned_data.get('for_coursework'),
            },
            'Carbonate PHI Nodes': {
                'phi_association': cleaned_data.get('phi_association'),
            },
            'cBioPortal': {
                'phi_association': cleaned_data.get('phi_association'),
                'access_level': cleaned_data.get('access_level'),
                'confirm_understanding': cleaned_data.get('confirm_understanding'),
            },
            'RStudio Connect': {
                'project_directory_name': cleaned_data.get('project_directory_name'),
                'confirm_understanding': cleaned_data.get('confirm_understanding'),
            },
            'Geode-Projects': {
                'storage_space': cleaned_data.get('storage_space'),
                'storage_space_unit': cleaned_data.get('storage_space_unit'),
                'start_date': cleaned_data.get('start_date'),
                'primary_contact': cleaned_data.get('primary_contact'),
                'secondary_contact': cleaned_data.get('secondary_contact'),
                'department_full_name': cleaned_data.get('department_full_name'),
                'department_short_name': cleaned_data.get('department_short_name'),
                'fiscal_officer': cleaned_data.get('fiscal_officer'),
                'account_number': cleaned_data.get('account_number'),
                'it_pros': cleaned_data.get('it_pros'),
                'devices_ip_addresses': cleaned_data.get('devices_ip_addresses'),
                'data_management_plan': cleaned_data.get('data_management_plan'),
                'use_indefinitely': cleaned_data.get('use_indefinitely'),
                'end_date': cleaned_data.get('end_date'),
            },
            'Slate-Project': {
                'first_name': cleaned_data.get('first_name'),
                'last_name': cleaned_data.get('last_name'),
                'campus_affiliation': cleaned_data.get('campus_affiliation'),
                'email': cleaned_data.get('email'),
                'project_directory_name': cleaned_data.get('project_directory_name'),
                'start_date': cleaned_data.get('start_date'),
                'store_ephi': cleaned_data.get('store_ephi'),
                'storage_space': cleaned_data.get('storage_space'),
                'account_number': cleaned_data.get('account_number'),
                'data_manager': cleaned_data.get('data_manager')
            },
            'Priority Boost': {
                'is_grand_challenge': cleaned_data.get('is_grand_challenge'),
                'system': cleaned_data.get('system'),
                'grand_challenge_program': cleaned_data.get('grand_challenge_program'),
                'end_date': cleaned_data.get('end_date'),
            },
        }
        resource = resources.get(resource_obj.name)
        if resource is None:
            return

        ldap_user_info_enabled = False
        if 'coldfront.plugins.ldap_user_info' in settings.INSTALLED_APPS:
            from coldfront.plugins.ldap_user_info.utils import check_if_user_exists
            ldap_user_info_enabled = True

        raise_error = False
        required_field_text = 'This field is required'
        for key, value in resource.items():
            resource_name = resource_obj.name

            # First check if the required field was filled in.
            if value is None or value == '' or value is False:
                # Handle special cases for missing required fields here before continuing.
                if resource_name == 'Geode-Projects':
                    if key == 'end_date' and resources[resource_name]['use_indefinitely']:
                        continue
                    elif key == 'use_indefinitely':
                        continue
                elif resource_name == 'Slate-Project':
                    if key == 'account_number' and resources[resource_name]['storage_space'] <= 15:
                        continue
                elif resource_name == 'Priority Boost':
                    system = resources[resource_name]['system']
                    is_grand_challenge = resources[resource_name]['is_grand_challenge']
                    if key == 'is_grand_challenge':
                        continue
                    elif key == 'end_date' and is_grand_challenge and system == 'BigRed3':
                        continue
                    elif key == 'grand_challenge_program' and (not is_grand_challenge or system == 'Carbonate'):
                        continue

                raise_error = True
                self.add_error(key, required_field_text)
                # If the value does not exist then no more value checking is needed.
                continue

            # General value checks for required fields should go here.
            if key == 'start_date':
                if value <= date.today():
                    raise_error = True
                    self.add_error(key, 'Please select a start date later than today')
                    continue
                end_date = resources[resource_name].get('end_date')
                if end_date and value >= end_date:
                    raise_error = True
                    self.add_error(key, 'Start date must be earlier than end date')
                    continue
            elif key == 'account_number':
                if not len(value) == 9:
                    raise_error = True
                    self.add_error(key, 'Account number must have a format of ##-###-##')
                    continue
                elif not value[2] == '-' or not value[6] == '-':
                    raise_error = True
                    self.add_error(key, 'Account number must have a format of ##-###-##')
                    continue
            elif key == 'storage_space':
                if value <= 0:
                    raise_error = True
                    self.add_error(key, 'Storage space must be greater than 0')
                    continue
            elif key == 'end_date':
                if value and value <= date.today():
                    raise_error = True
                    self.add_error(key, 'Please select an end date later than today')
                    continue
            elif key == 'project_directory_name':
                if not value.isalnum():
                    raise_error = True
                    self.add_error(key, 'Project directory name must be alphanumeric')
                    continue
            elif key == 'data_manager':
                manager_exists = self.project_obj.projectuser_set.filter(
                    user__username=value,
                    role__name='Manager',
                    status__name='Active'
                ).exists()
                if not manager_exists:
                    raise_error = True
                    self.add_error(key, 'Data Manager must be a project Manager')
                    continue

                check_resource_account = resource_obj.get_attribute('check_user_account')
                if check_resource_account and not resource_obj.check_user_account_exists(value, check_resource_account):
                    raise_error = True
                    self.add_error(
                        key,
                        format_html(
                            """
                            Data Manager must have a Slate-Project account. They can create one
                            <a href="https://access.iu.edu/Accounts/Create">here</a>
                            """
                        )
                    )
                    continue

            # Value checks for a specific resource's required fields should go here.
            if resource_name == 'Geode-Projects':
                if key == 'storage_space':
                    unit = resources[resource_name]['storage_space_unit']
                    if value <= 0 and unit == 'TB' or value < 200 and unit == 'GB':
                        raise_error = True
                        self.add_error(key, 'Please enter a storage amount greater than or equal to 200GB')
                        continue
                elif key in ['primary_contact', 'secondary_contact', 'fiscal_officer']:
                    user_exists = True
                    if ldap_user_info_enabled:
                        user_exists = check_if_user_exists(value)

                    if not user_exists:
                        raise_error = True
                        self.add_error(key, 'This username is not valid')
                        continue
                elif key == 'it_pros':
                    invalid_users = []
                    for username in value.split(','):
                        user_exists = True
                        if ldap_user_info_enabled:
                            user_exists = check_if_user_exists(username)

                        if not user_exists:
                            invalid_users.append(username)

                    if invalid_users:
                        raise_error = True
                        self.add_error(key, 'Username(s) {} are not valid'.format(
                            ', '.join(invalid_users)
                            ))
                        continue
            elif resource_name == 'Slate-Project':
                if key == 'data_manager':
                    if users and value != self.request_user.username:
                        raise_error = True
                        self.add_error(
                            'users',
                            'Only the data manager can add users to a Slate-Project resource'
                        )
                        continue

        if raise_error:
            raise ValidationError('Please correct the errors below')


class AllocationUpdateForm(forms.Form):
    status = forms.ModelChoiceField(
        queryset=AllocationStatusChoice.objects.all().order_by('name'), empty_label=None)
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    description = forms.CharField(max_length=512,
                                  label='Description',
                                  required=False)
    is_locked = forms.BooleanField(required=False)
    is_changeable = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(
                'End date cannot be less than start date'
            )


class AllocationInvoiceUpdateForm(forms.Form):
    status = forms.ModelChoiceField(queryset=AllocationStatusChoice.objects.filter(name__in=[
        'Payment Pending', 'Payment Requested', 'Payment Declined', 'Paid']).order_by('name'), empty_label=None)


class AllocationAddUserForm(forms.Form):
    username = forms.CharField(max_length=150, disabled=True)
    first_name = forms.CharField(max_length=30, required=False, disabled=True)
    last_name = forms.CharField(max_length=150, required=False, disabled=True)
    email = forms.EmailField(max_length=100, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)


class AllocationRemoveUserForm(forms.Form):
    username = forms.CharField(max_length=150, disabled=True)
    first_name = forms.CharField(max_length=30, required=False, disabled=True)
    last_name = forms.CharField(max_length=150, required=False, disabled=True)
    email = forms.EmailField(max_length=100, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, disable_selected, **kwargs):
        super().__init__(*args, **kwargs)
        if disable_selected:
            self.fields['selected'].disabled = True


class AllocationRemoveUserFormset(forms.BaseFormSet):
    def get_form_kwargs(self, index):
        """
        Override so specific users can be prevented from being removed.
        """
        kwargs = super().get_form_kwargs(index)
        disable_selected = kwargs['disable_selected'][index]
        return {'disable_selected': disable_selected}

class AllocationAttributeDeleteForm(forms.Form):
    pk = forms.IntegerField(required=False, disabled=True)
    name = forms.CharField(max_length=150, required=False, disabled=True)
    value = forms.CharField(max_length=150, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pk'].widget = forms.HiddenInput()


class AllocationSearchForm(forms.Form):
    project = forms.CharField(label='Project Title',
                              max_length=100, required=False)
    username = forms.CharField(
        label='Username', max_length=100, required=False)
    resource_type = forms.ModelChoiceField(
        label='Resource Type',
        queryset=ResourceType.objects.all().order_by('name'),
        required=False)
    resource_name = forms.ModelMultipleChoiceField(
        label='Resource Name',
        queryset=Resource.objects.filter(
            is_allocatable=True).order_by('name'),
        required=False)
    allocation_attribute_name = forms.ModelChoiceField(
        label='Allocation Attribute Name',
        queryset=AllocationAttributeType.objects.all().order_by('name'),
        required=False)
    allocation_attribute_value = forms.CharField(
        label='Allocation Attribute Value', max_length=100, required=False)
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    active_from_now_until_date = forms.DateField(
        label='Active from Now Until Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    status = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=AllocationStatusChoice.objects.all().order_by('name'),
        required=False)
    show_all_allocations = forms.BooleanField(initial=False, required=False)


class AllocationInvoiceSearchForm(forms.Form):
    resource_type = forms.ModelChoiceField(
        label='Resource Type',
        queryset=ResourceType.objects.all().order_by('name'),
        required=False
    )
    resource_name = forms.ModelMultipleChoiceField(
        label='Resource Name',
        queryset=Resource.objects.filter(is_allocatable=True).order_by('name'),
        required=False
    )
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False
    )


class AllocationInvoiceExportForm(forms.Form):
    file_name = forms.CharField(max_length=64, initial='invoices')
    resource = forms.ChoiceField(choices=())
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False
    )

    def __init__(self, *args, resources=None, **kwargs):
        super().__init__(*args, **kwargs)

        if resources is None:
            self.fields['resource'].choices = ()
        else:
            self.fields['resource'].choices = resources


class AllocationReviewUserForm(forms.Form):
    # No relation to AllocationUserReview model.
    ALLOCATION_REVIEW_USER_CHOICES = (
        ('keep_in_allocation_and_project', 'Keep in allocation and project'),
        ('keep_in_project_only', 'Remove from this allocation only'),
        ('remove_from_project', 'Remove from project'),
    )

    username = forms.CharField(max_length=150, disabled=True)
    first_name = forms.CharField(max_length=30, required=False, disabled=True)
    last_name = forms.CharField(max_length=150, required=False, disabled=True)
    email = forms.EmailField(max_length=100, required=False, disabled=True)
    user_status = forms.ChoiceField(choices=ALLOCATION_REVIEW_USER_CHOICES)


class AllocationInvoiceNoteDeleteForm(forms.Form):
    pk = forms.IntegerField(required=False, disabled=True)
    note = forms.CharField(widget=forms.Textarea, disabled=True)
    author = forms.CharField(
        max_length=512, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pk'].widget = forms.HiddenInput()


class AllocationAccountForm(forms.ModelForm):

    class Meta:
        model = AllocationAccount
        fields = ['name', ]


class AllocationAttributeChangeForm(forms.Form):
    pk = forms.IntegerField(required=False, disabled=True)
    name = forms.CharField(max_length=150, required=False, disabled=True)
    value = forms.CharField(max_length=150, required=False, disabled=True)
    new_value = forms.CharField(max_length=150, required=False, disabled=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pk'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('new_value') != "":
            allocation_attribute = AllocationAttribute.objects.get(pk=cleaned_data.get('pk'))
            allocation_attribute.value = cleaned_data.get('new_value')
            allocation_attribute.clean()


class AllocationAttributeUpdateForm(forms.Form):
    change_pk = forms.IntegerField(required=False, disabled=True)
    attribute_pk = forms.IntegerField(required=False, disabled=True)
    name = forms.CharField(max_length=150, required=False, disabled=True)
    value = forms.CharField(max_length=150, required=False, disabled=True)
    new_value = forms.CharField(max_length=150, required=False, disabled=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['change_pk'].widget = forms.HiddenInput()
        self.fields['attribute_pk'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        allocation_attribute = AllocationAttribute.objects.get(pk=cleaned_data.get('attribute_pk'))

        allocation_attribute.value = cleaned_data.get('new_value')
        allocation_attribute.clean()


class AllocationChangeForm(forms.Form):
    EXTENSION_CHOICES = [
        (0, "No Extension")
    ]
    for choice in ALLOCATION_CHANGE_REQUEST_EXTENSION_DAYS:
        EXTENSION_CHOICES.append((choice, "{} days".format(choice)))

    end_date_extension = forms.TypedChoiceField(
        label='Request End Date Extension',
        choices = EXTENSION_CHOICES,
        coerce=int,
        required=False,
        empty_value=0,)
    justification = forms.CharField(
        label='Justification for Changes',
        widget=forms.Textarea,
        required=True,
        help_text='Justification for requesting this allocation change request.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AllocationChangeNoteForm(forms.Form):
        notes = forms.CharField(
            max_length=512, 
            label='Notes', 
            required=False, 
            widget=forms.Textarea,
            help_text="Leave any feedback about the allocation change request.")

