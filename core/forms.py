# core/forms.py

from django import forms
from .models import CV

class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = [ 'image','full_name', 'email', 'phone_number', 'address', 'experience', 'education', 'projects', 'skills', 'awards', 'languages']
