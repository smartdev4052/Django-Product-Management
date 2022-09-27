from django.contrib import messages
from django.shortcuts import redirect, render
from notification.forms import NotificationCreateForm, NotificationEditForm
from notification.models import Notification
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _


@login_required
def notification_index_view(request):
    user = request.user
    notifications = Notification.objects.filter(recipient=user)
    context = {}
    context['notifications'] = notifications
    return render(request, 'notification/index.html', context)


@login_required
def notification_detail_view(request, id):
    user = request.user
    notification = Notification.objects.filter(id=id, recipient=user).first()
    Notification.objects.filter(id=id, recipient=user).update(is_read=True)
    context = {}
    context['notification'] = notification
    return render(request, 'notification/detail.html', context)


@login_required
def notification_create_view(request):
    if request.method == 'POST':
        form = NotificationCreateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.source = request.user
            #obj.project = project
            # obj.save()
            form.save()
            messages.success(request, 'Succesfully')
            return redirect('notification:notification_index')
    else:
        form = NotificationCreateForm()

    return render(request, 'notification/create.html', {'form': form})


@login_required
def notification_edit_view(request, id):
    notification = Notification.objects.filter(id=id).first()
    if request.method == 'POST':
        form = NotificationEditForm(request.POST, instance=notification)
        if form.is_valid():
            #obj = form.save(commit=False)
            #obj.user = request.user
            # obj. = project
            # obj.save()
            form.save()
            messages.success(request, 'Succesfully')
            return redirect('notification:notification_index')
    else:
        form = NotificationEditForm(instance=notification)

    return render(request, 'notification/edit.html', {'form': form})
