from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields.related import ManyToManyField
from client.models import Client
from shop.models import Product
import jsonfield
from private_storage.fields import PrivateFileField
from django.utils.translation import ugettext_lazy as _
import os

PERMISSION_TYPE = (
    ('1', _('Reader')),
    ('2', _('Editor')),
)

TASK_STATUS = (
    ('IN_PROGRESS', _('In progress')),
    ('INCOMPLETE', _('Incomplete')),
    ('REVIEW', _('Review')),
    ('COMPLETE', _('Complete'))
)

FILE_TYPE = (
    ('NOTE', _('Note')),
    ('TASK', _('Task')),
    ('TASK_NOTE', _('Task note')),
    ('MESSAGE', _('Message')),
    ('MEET', _('Meet')),
    ('MEET_NOTE', _('Meet note')),
    ('FORM', _('Form')),
    ('FORM_NOTE', _('Form note')),
    ('DEFAULT', _('Default'))
)

NOTE_TYPE = (
    ('TASK', _('Task')),
    ('MEET', _('Meet')),
    ('NOTE', _('Note')),
    ('FORM', _('Form'))
)


class Project(models.Model):
    name = models.CharField(max_length=254)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, related_name='project_client')
    description = models.TextField(null=True, blank=True)
    closed_description = models.TextField(null=True, blank=True)
    order_number = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='project_created_by')
    responsible_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='project_responsible_user')  # felelős
    archived = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.name)


class Meet(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name='meet_project')
    name = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    google_calendar_id = models.CharField(max_length=254, null=True, blank=True)
    url = models.CharField(max_length=254, null=True, blank=True)
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='meet_from_user')
    to_user = models.ManyToManyField(User)
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    meet_start = models.DateTimeField(null=True)
    meet_end = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # file

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ('-created_at',)


class Task(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name='task_project')
    name = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='task_from_user')
    responsible_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='task_responsible_user')  # felelős
    to_user = models.ManyToManyField(User, blank=True)
    status = models.CharField(
        choices=TASK_STATUS, max_length=254, default='IN_PROGRESS')
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    archived = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def full_name(self):
        return self.responsible_user.get_full_name()

    def __str__(self):
        return str(self.name)


class TaskDefault(models.Model):
    product = ManyToManyField(Product)
    name = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField(null=True)
    start_date_plus_day = models.PositiveIntegerField(null=True, blank=True)
    product = ManyToManyField(Product)

    def __str__(self):
        return str(self.name)


class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                null=True, blank=True, related_name='message_project')
    content = models.TextField(null=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='message_from_user')
    url = models.CharField(max_length=254, null=True, blank=True)
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return str(self.content)


class Activity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                null=True, blank=True, related_name='activity_project')
    name = models.CharField(max_length=254, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='activity_user')
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.name)


# itt kezdődőtt a Invite model csak át leltt rakva a task kezelés maitt és alatta jött ez a team type
class TeamType(models.Model):
    name = models.CharField(max_length=254)
    # project_form = 					models.ManyToManyField(ProjectFormDefault) # formot kérjük a product heylett, és ide az alap formokat töltjük majd be ami hozzá van vonva/ ha elfogadja hogy yes akkor kiraly omnnatol ugynaugy hozzá
    # hozzátesszük az embert a formhoz mnit tag.

    def __str__(self):
        return str(self.name)


class ProjectFormDefault(models.Model):
    name = models.CharField(max_length=254, null=True, blank=True)
    question = models.CharField(max_length=254, null=True, blank=True)
    button_text = models.CharField(max_length=254, null=True, blank=True)
    default_schema = models.JSONField(null=True, blank=True)
    default_meta = models.JSONField(null=True, blank=True)
    # ez mnodja meg hogy pl a form az mindig jöjjön létre vagy csak akkor ha 25% os ügyfelet rendelek pl hozzá
    default_form = models.BooleanField(default=False)
    product = ManyToManyField(Product)
    start_date_plus_day = models.PositiveIntegerField(null=True, blank=True)
    multiple = models.BooleanField(default=False)
    team_type = ManyToManyField(TeamType, blank=True)  # max törölni

    def __str__(self):
        return str(self.name)


class ProjectForm(models.Model):
    name = models.CharField(max_length=254, null=True, blank=True)
    question = models.CharField(max_length=254, null=True, blank=True)
    button_text = models.CharField(max_length=254, null=True, blank=True)
    form_schema = models.JSONField(null=True, blank=True)
    form_meta = models.JSONField(null=True, blank=True)
    form_value = models.JSONField(null=True, blank=True)
    project = models.ForeignKey(
        Project, related_name='project_form', blank=True, null=True, on_delete=models.CASCADE)
    locked = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    to_user = models.ManyToManyField(User, blank=True)
    responsible_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='project_form_responsible_user')
    start_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    help_link = models.CharField(max_length=254, null=True, blank=True)
    multiple = models.BooleanField(default=False)
    draft = models.BooleanField(default=False)
    clone = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class DocumentDefault(models.Model):
    name = models.CharField(max_length=254, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    #description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_by_document')
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Document(models.Model):
    name = models.CharField(max_length=254, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    #description = models.TextField(null=True, blank=True)
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='from_user_document')
    project = models.ForeignKey(
        Project, related_name='project_document', blank=True, null=True, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    to_user = models.ManyToManyField(User)
    #data_from_form = models.ForeignKey(ProjectForm, on_delete=models.CASCADE, null=True, blank=True, related_name='form_default_document')
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Invite(models.Model):
    sender = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    sender_display_name = models.CharField(max_length=254, null=True)
    recipient = models.ForeignKey(
        User, related_name='invite_recipient', blank=True, null=True, on_delete=models.CASCADE)
    invite_email = models.CharField(max_length=254, null=True, blank=True) # erre is ráeelenörzök meghivásnál (task, form, document) kiegészítő mező
    action = models.CharField(max_length=254)
    description = models.TextField()
    project = models.ForeignKey(
        Project, related_name='invite_project', blank=True, null=True, on_delete=models.CASCADE)
    meet_start = models.DateTimeField(null=True)
    meet_end = models.DateTimeField(null=True)
    # Added in 2022.02
    task = ManyToManyField(Task, blank=True)
    project_form = ManyToManyField(ProjectForm, blank=True)
    meet = ManyToManyField(Meet, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('create_date',)

    def __str__(self):
        return str(self.description)


#
class Team(models.Model):
    email = models.EmailField(null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='team_user')
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, related_name='team_project')
    role = models.CharField(choices=PERMISSION_TYPE,
                            max_length=50, default='1')
    active = models.BooleanField(default=False)
    team_type = models.ForeignKey(
        TeamType, on_delete=models.CASCADE, null=True, related_name='team_type')
    # akik alabol létrejönnke ők nem törölhetpej azaz Falseok
    is_removable = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    # ezt csak a vásásrló kapja meg ez ek alapján jön létre formok ki mit lathat
    customer = models.BooleanField(default=False)
    token = models.UUIDField(blank=True, null=True)  # editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', )

    
    def __str__(self):
        return str(self.user)
        
    """

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    """

class Note(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name='note_project')
    content = models.TextField(null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='note_user')
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='note_meet')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='note_task')
    project_form = models.ForeignKey(ProjectForm, on_delete=models.CASCADE,
                                     null=True, blank=True, related_name='note_project_form')
    private = models.BooleanField(default=False)  # privát vagy nem privát
    type = models.CharField(choices=NOTE_TYPE, max_length=254, default='NOTE')
    visible = models.BooleanField(default=True)
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.content)

    class Meta:
        ordering = ('-created_at', )


def get_file_path_default(instance, filename):
    today = timezone.now().date()
    project_id = str(instance.project.id)
    ext = filename.split('.')[-1]
    file_name = filename.split('.')[0]
    filename = "%s-%s.%s" % (today, file_name, ext)
    path = str('project/' + project_id)
    return os.path.join(path, filename)


class File(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name='file_project')
    name = models.CharField(max_length=254)
    project_file = PrivateFileField(
        null=True, blank=True, upload_to=get_file_path_default)
    description = models.TextField(null=True, blank=True)
    is_relase = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='file_from_user')
    note = models.ForeignKey(Note, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='file_note')
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='file_meet')
    project_form = models.ForeignKey(ProjectForm, on_delete=models.CASCADE,
                                     null=True, blank=True, related_name='file_form')
    meet_record_url = models.CharField(max_length=254, blank=True, null=True)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, null=True, blank=True, related_name='file_message')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='file_task')
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    lawyer_mode = models.BooleanField(default=False)
    file_type = models.CharField(
        choices=FILE_TYPE, max_length=254, default='DEFAULT')
    archived = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)
