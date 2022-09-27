from account.models import Profile
from notification.models import Notification
from django.db.models import Q
from django.conf import settings
from order.models import Order
from project.models import Activity, Invite, Meet, Task, Team
from datetime import datetime
from django.utils import timezone

# optimalizálni külön minden user tipusra


def user_info(request):
    #now = datetime.now()
    now = datetime.now(tz=timezone.utc)
    user = request.user
    if user.is_authenticated:

        profile = Profile.objects.filter(user=user).first()

        # COUNT
        order_count = Order.objects.filter(is_read=False).count()
        invite_count = Invite.objects.filter(
            is_read=False, recipient=user).count()
        meet_count = Meet.objects.filter(
            to_user=user).filter(meet_start__gte=now).count()
        task_count = Task.objects.filter(
            to_user=user).exclude(status='COMPLETE').count()

        # TODO:| Q(level='GLOBAL'), is_read = False
        profile_notifications = (Notification.objects
                                 .filter(Q(recipient=user, is_read=False))
                                 .select_related('recipient')
                                 .select_related('sender').
                                 exclude()
                                 ).order_by('-create_date')

        profile_notifications_count = profile_notifications.count()

        # Activity
        user = request.user
        team = Team.objects.filter(user=user).values_list(
            'project_id', flat=True)
        if user.profile.user_role == 1:
            activities = Activity.objects.filter(
                project__in=team, is_read=False).exclude(lawyer_mode=True)[0:10]

        elif user.profile.user_role == 2:
            activities = Activity.objects.filter(
                project__in=team, is_read=False)[0:10]

        else:
            activities = []

        if user.is_authenticated:
            profile_image = profile.profile_image.url

        return {'profile_image': profile_image,
                'meet_count': meet_count,
                'task_count': task_count,
                'order_count': order_count,
                'invite_count': invite_count,
                'profile_notifications': profile_notifications,
                'profile_notifications_count': profile_notifications_count,
                'activities': activities

                }
    return {}

# Get site url

def site(request):
    return {'SITE_URL': settings.SITE_URL}