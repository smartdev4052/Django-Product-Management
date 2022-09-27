from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Account type:
# 1 User
# 2 Lawyer
# 3 Office
# 4 Admin

"""
PROFILE MODEL
"""


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # kreátor
    profile_image = models.ImageField(null=True, blank=True, upload_to='profile_image',
                                      default='profile_image/default.jpeg', verbose_name='Profile Image')
    calendar_id = models.CharField(max_length=254, null=True, blank=True)
    office = models.CharField(max_length=254, null=True, blank=True)
    user_role = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user)


"""
AUTOMATE SAVE PROFILE AND USER
"""


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
