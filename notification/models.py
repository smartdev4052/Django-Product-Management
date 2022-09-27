from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator
from django.db.models.fields.related import ForeignKey

from project.models import Project
from django.utils.translation import ugettext_lazy as _

NOTIFY_LEVEL = (
    ('INFO', _('INFO')),
    ('WARNING', _('WARNING')),
    ('ERROR', _('ERROR')),
    ('SUCCESS', _('SUCCESS'))
)


class Notification(models.Model):
    sender = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    sender_display_name = models.CharField(max_length=254, null=True)
    recipient = models.ForeignKey(
        User, related_name='recipient_notification', blank=True, null=True, on_delete=models.CASCADE)
    action = models.CharField(max_length=254)
    level = models.CharField(choices=NOTIFY_LEVEL, max_length=50)
    description = models.TextField(validators=[MaxLengthValidator(300)])
    is_read = models.BooleanField(default=False, db_index=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('create_date',)

    def __str__(self):
        if self.sender:
            res = '{}: {} {} {} => {}'.format(
                self.level,
                self.sender,
                self.action,
                self.description,
                self.recipient,
            )
        else:
            res = self.description

        return res
