from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from account.models import Profile
from django.utils.translation import ugettext_lazy as _

"""
USER CREATE FRO AUTH
"""


def ForbiddenUsers(value):
    forbidden_users = ['admin', 'css', 'js', 'authenticate', 'login', 'logout', 'administrator', 'root',
                                       'email', 'user', 'join', 'sql', 'static', 'python', 'delete']
    if value.lower() in forbidden_users:
        raise ValidationError(_('Ez a felhasználónév nem engedélyezett.'))


def InvalidUser(value):
    if '@' in value or '+' in value or '-' in value:
        raise ValidationError(_('Nem engedélyezett karakterek: @ , - , + '))


def UniqueEmail(value):
    if User.objects.filter(email__iexact=value).exists():
        raise ValidationError(_('Ez az e-mail cím már foglalt.'))


def UniqueUser(value):
    if User.objects.filter(username__iexact=value).exists():
        raise ValidationError(_('Ez a felhasználónév már foglalt.'))


class RegisterForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
    ), max_length=30, required=True, label=_('Username'))
    email = forms.CharField(widget=forms.EmailInput(),
                            max_length=100, required=True, label=_('E-mail'))
    first_name = forms.CharField(widget=forms.TextInput(
    ), max_length=30, required=True, label=_('First Name'))
    last_name = forms.CharField(widget=forms.TextInput(
    ), max_length=30, required=True, label=_('Last Name'))
    password = forms.CharField(
        widget=forms.PasswordInput(), label=_('Password'))
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(), required=True, label=_("Password repeat"))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].validators.append(ForbiddenUsers)
        self.fields['username'].validators.append(InvalidUser)
        self.fields['username'].validators.append(UniqueUser)
        self.fields['email'].validators.append(UniqueEmail)

    def clean(self):
        super(RegisterForm, self).clean()
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            self._errors['password'] = self.error_class(
                [_('A jelszavak nem egyeznek, kérjük add meg újra!')])
        return self.cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=63, label=_('Username'), widget=forms.TextInput(
        attrs={'autofocus': True, 'autocomplete': 'off'}))
    password = forms.CharField(
        max_length=63, widget=forms.PasswordInput, label=_('Password'))


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
