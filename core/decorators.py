from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

"""
USER ROLE
"""


def user_role(view_func):
    def wrap(request, *args, **kwargs):
        user_role = request.user.profile.user_role
        if user_role == 0:
            messages.success(
                request, _('Kérünk töltsd ki a csillagal jelölt mezőket!'))
            return redirect('account:my_profile')
        else:
            return view_func(request, *args, **kwargs)
    return wrap


def is_lawyer(view_func):
    def wrap(request, *args, **kwargs):
        user_role = request.user.profile.user_role
        if user_role == 2:
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(request, _(
                'Cant acces'))
            return redirect('project:project_index')
    return wrap

def is_office(view_func):
    def wrap(request, *args, **kwargs):
        user_role = request.user.profile.user_role
        if user_role == 3:
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(request, _(
                'Cant acces'))
            return redirect('project:project_index')
    return wrap
