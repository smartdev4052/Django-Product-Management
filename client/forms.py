from django import forms
from .models import Client


class ClientCreateForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"
        exclude = ['user', 'archived']