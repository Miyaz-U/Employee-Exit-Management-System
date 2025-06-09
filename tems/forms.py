from django import forms
from .models import Resignation, Feedback
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import ResignationExtras, EmployeeBasic, Resignation


class ResignForm(forms.ModelForm):
    class Meta:
        model = Resignation
        fields = ['reason']
        
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        exclude = ['user', 'resign_id']

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Required")
    last_name = forms.CharField(max_length=30, required=True, help_text="Required")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]
        def clean_email(self):
            email = self.cleaned_data.get("email")
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Email already exists. Please use a different email.")
            return email

        def save(self, commit=True):
            user = super().save(commit=False)
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.email = self.cleaned_data["email"]
            if commit:
                user.save()
            return user
        
# ✅ Custom Admin Form for EmployeeBasic
class EmployeeBasicAdminForm(forms.ModelForm):
    class Meta:
        model = EmployeeBasic
        fields = '__all__'

    def clean_emp_dob(self):
        emp_dob = self.cleaned_data['emp_dob']
        if isinstance(emp_dob, str):
            try:
                emp_dob = datetime.strptime(emp_dob, "%Y-%m-%d").date()
            except ValueError:
                raise forms.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return emp_dob
        

'''class AssignResignationForm(forms.ModelForm):
    #hr_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='hr'), label="HR SPOC", required=False)
    manager_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='manager'), label="Manager SPOC", required=False)
    IT_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='it'), label="IT SPOC", required=False)
    finance_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='finance'), label="Finance SPOC", required=False)
    security_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='security'), label="Security SPOC", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['manager_spoc_id', 'IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']:
            self.fields[field].label_from_instance = lambda obj: f"{obj.username} - {obj.first_name} {obj.last_name}"

    class Meta:
        model = ResignationExtras
        fields = ['manager_spoc_id', 'IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']'''

class AssignResignationForm(forms.ModelForm):
    #manager_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='manager'), label="Manager SPOC", required=False)
    IT_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='it'), label="IT SPOC", required=False)
    finance_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='finance'), label="Finance SPOC", required=False)
    security_spoc_id = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='security'), label="Security SPOC", required=False)
    
    def __init__(self, *args, **kwargs):
        resignation_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
            
        if resignation_instance:
            resigned_user = resignation_instance.resignation.emp_code.user
            #self.fields['manager_spoc_id'].queryset = self.fields['manager_spoc_id'].queryset.exclude(id=resigned_user.id)
            self.fields['IT_spoc_id'].queryset = self.fields['IT_spoc_id'].queryset.exclude(id=resigned_user.id)
            self.fields['finance_spoc_id'].queryset = self.fields['finance_spoc_id'].queryset.exclude(id=resigned_user.id)
            self.fields['security_spoc_id'].queryset = self.fields['security_spoc_id'].queryset.exclude(id=resigned_user.id)
                
        '''for field in ['manager_spoc_id', 'IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']:
            self.fields[field].label_from_instance = lambda obj: f"{obj.username} - {obj.first_name} {obj.last_name}"'''
        for field in ['IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']:
            self.fields[field].label_from_instance = lambda obj: f"{obj.username} - {obj.first_name} {obj.last_name}"
    class Meta:
        model = ResignationExtras
        #fields = ['manager_spoc_id', 'IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']
        fields = ['IT_spoc_id', 'finance_spoc_id', 'security_spoc_id']