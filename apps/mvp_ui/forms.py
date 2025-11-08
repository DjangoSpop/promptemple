"""
Django forms for MVP UI
Maps OpenAPI request schemas to Django forms
"""
from django import forms
from django.core.validators import MinLengthValidator


class TemplateCreateForm(forms.Form):
    """Form for creating templates"""
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter template title',
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your template',
        })
    )
    content = forms.CharField(
        required=True,
        validators=[MinLengthValidator(10)],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter template content with {{variables}}',
        })
    )
    category = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_public = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas',
        })
    )


class TemplateSearchForm(forms.Form):
    """Form for searching templates"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search templates...',
        })
    )
    category = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_public = forms.NullBooleanField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    ordering = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Default'),
            ('title', 'Title A-Z'),
            ('-title', 'Title Z-A'),
            ('created_at', 'Oldest First'),
            ('-created_at', 'Newest First'),
            ('usage_count', 'Least Used'),
            ('-usage_count', 'Most Used'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class UserLoginForm(forms.Form):
    """Form for user login"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    remember = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserRegistrationForm(forms.Form):
    """Form for user registration"""
    username = forms.CharField(
        max_length=150,
        required=True,
        validators=[MinLengthValidator(3)],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        required=True,
        validators=[MinLengthValidator(8)],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password (min 8 characters)',
            'autocomplete': 'new-password',
        })
    )
    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data


class UserProfileForm(forms.Form):
    """Form for updating user profile"""
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about yourself',
        })
    )


class ResearchJobForm(forms.Form):
    """Form for creating research jobs"""
    query = forms.CharField(
        required=True,
        validators=[MinLengthValidator(10)],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your research question...',
        })
    )
    depth = forms.ChoiceField(
        required=False,
        choices=[
            ('basic', 'Basic'),
            ('standard', 'Standard'),
            ('deep', 'Deep'),
        ],
        initial='standard',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    max_results = forms.IntegerField(
        required=False,
        initial=5,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5',
        })
    )
