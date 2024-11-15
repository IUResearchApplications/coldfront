from datetime import date

from django import forms
from django.forms.widgets import RadioSelect
from coldfront.plugins.slate_project.validators import ValidateDirectoryName, ValidateDupDirectoryName, ValidateAccountNumber


class SlateProjectSearchForm(forms.Form):
    SLATE_PROJECT = 'Slate Project'
    slate_project = forms.CharField(label=SLATE_PROJECT, min_length=2, max_length=30)


class SlateProjectForm:
    YES_NO_CHOICES = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    CAMPUS_CHOICES = (
        ('', ''),
        ('BL', 'BL'),
        ('IN', 'IN'),
        ('CO', 'CO'),
        ('EA', 'EA'),
        ('FW', 'FW'),
        ('KO', 'KO'),
        ('NW', 'NW'),
        ('SB', 'SB'),
        ('SE', 'SE'),
    )
    STORAGE_QUANTITY_CHOICES = (
        (num, num) for num in range(31)
    )

    first_name = forms.CharField(max_length=40, disabled=True)
    last_name = forms.CharField(max_length=40, disabled=True)
    campus_affiliation = forms.ChoiceField(choices=CAMPUS_CHOICES)
    email = forms.EmailField(max_length=40, disabled=True)
    project_directory_name = forms.CharField(
        max_length=23, validators=[ValidateDirectoryName(), ValidateDupDirectoryName()]
    )
    description = forms.CharField(widget=forms.Textarea)
    placeholder1 = forms.CharField(max_length=100, initial='placeholder1')
    placeholder2 = forms.CharField(max_length=100, initial='placeholder2')
    placeholder3 = forms.CharField(max_length=100, initial='placeholder3')
    storage_space = forms.IntegerField(min_value=1, max_value=30, widget=forms.Select(choices=STORAGE_QUANTITY_CHOICES))
    start_date = forms.DateField(disabled=True)
    account_number = forms.CharField(max_length=9, initial='00-000-00', validators=[ValidateAccountNumber()])
    store_ephi = forms.ChoiceField(choices=YES_NO_CHOICES, widget=RadioSelect)

    def __init__(self, request_user, resource_attributes, project_obj, resource_obj, *args, **kwargs):
        super().__init__(request_user, resource_attributes, project_obj, resource_obj, *args, **kwargs)

        self.fields['first_name'].initial = request_user.first_name
        self.fields['last_name'].initial = request_user.last_name
        self.fields['email'].initial = request_user.email
        self.fields['start_date'].initial = date.today()

        self.fields['project_directory_name'].widget.attrs.update({'placeholder': 'example_A-Za-z0-9'})

        for field in self.errors:
            self.fields[field].widget.attrs.update({'autofocus': ''})
            break
