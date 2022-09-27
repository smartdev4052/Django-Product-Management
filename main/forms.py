from django import forms
from main.models import Page
from project.models import DocumentDefault

class PageCreateForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = "__all__"
        


class PageEditForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = "__all__"


class DocumentDefaultCreateForm(forms.ModelForm):
    class Meta:
        model = DocumentDefault
        fields = "__all__"
        exclude = ['created_by']
        


class DocumentDefaultEditForm(forms.ModelForm):
    class Meta:
        model = DocumentDefault
        fields = "__all__"
        exclude = ['created_by']