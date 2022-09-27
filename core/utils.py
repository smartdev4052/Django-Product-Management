from collections import namedtuple
from django.template.loader import render_to_string
from django.core.mail import send_mail
from smtplib import SMTPException

from notification.models import Notification
from project.models import Activity


class SignalSystem():
    # Email
    def email(to_user, subject, template, context):

        if template == '':
            template = 'default.html'
        else:
            template = template

        msg_html = render_to_string(f'email/{template}', context)

        try:
            send_mail(subject, '', 'Legisly <info@legisly.com>',
                      [to_user], fail_silently=True, html_message=msg_html,)
        except SMTPException as e:
            # TODO: error handling
            pass

        return

    # Notification

    def notification(sender, sender_display_name, recipient, action, level, description):

        try:
            Notification.objects.create(sender=sender, sender_display_name=sender_display_name,
                                        recipient=recipient, action=action, level=level, description=description)
        except:
            # TODO: error handling
            pass

        return

    def activity(project, name, description, user, lawyer_mode):
        try:
            Activity.objects.create(project=project, name=name,
                                    description=description, user=user, lawyer_mode=lawyer_mode)
        except:
            # TODO: error handling
            pass

        return
