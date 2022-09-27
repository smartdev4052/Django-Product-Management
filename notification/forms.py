from django import forms
from notification.models import Notification


class NotificationCreateForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = "__all__"
        exclude = ['source']


class NotificationEditForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = "__all__"