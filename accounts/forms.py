from django import forms
from .models import UserSettings


class UserSettingsForm(forms.ModelForm):
    """Form for user settings configuration"""
    
    class Meta:
        model = UserSettings
        fields = [
            'radarr_url', 'radarr_api_key', 'sonarr_url', 'sonarr_api_key',
            'server_type', 'server_url', 'server_api_key', 'theme'
        ]
        
        widgets = {
            'radarr_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'http://localhost:7878'
            }),
            'radarr_api_key': forms.PasswordInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Radarr API Key'
            }),
            'sonarr_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'http://localhost:8989'
            }),
            'sonarr_api_key': forms.PasswordInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Sonarr API Key'
            }),
            'server_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'server_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'http://localhost:8096'
            }),
            'server_api_key': forms.PasswordInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your API Key or Token'
            }),
            'theme': forms.Select(attrs={
                'class': 'form-input'
            })
        }
        
        labels = {
            'radarr_url': 'Radarr URL',
            'radarr_api_key': 'API Key',
            'sonarr_url': 'Sonarr URL',
            'sonarr_api_key': 'API Key',
            'server_type': 'Server Type',
            'server_url': 'Server URL',
            'server_api_key': 'API Key/Token',
            'theme': 'Theme'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except theme
        for field_name, field in self.fields.items():
            if field_name != 'theme':
                field.required = False
    
    def clean(self):
        """Remove empty values from cleaned_data so they don't overwrite existing values"""
        cleaned_data = super().clean()
        
        # List of fields that should only be updated if they have values
        conditional_fields = [
            'radarr_url', 'radarr_api_key', 'sonarr_url', 'sonarr_api_key',
            'server_type', 'server_url', 'server_api_key'
        ]
        
        # Remove empty values from cleaned_data so they don't get saved
        for field_name in conditional_fields:
            if field_name in cleaned_data:
                value = cleaned_data[field_name]
                if not value or (isinstance(value, str) and value.strip() == ''):
                    # Remove empty values from cleaned_data
                    del cleaned_data[field_name]
        
        return cleaned_data
    
    def save(self, commit=True):
        """Only save fields that have non-empty values"""
        instance = self.instance
        
        # Update only the fields that are present in cleaned_data
        # (empty fields have been removed by the clean() method)
        for field_name, value in self.cleaned_data.items():
            setattr(instance, field_name, value)
        
        if commit:
            instance.save()
        
        return instance