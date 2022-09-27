from django import forms
from .models import Meet, Message, Note, Project, Team, Task, File, Document, DocumentDefault, ProjectFormDefault, ProjectForm
from shop.models import Product
from django.utils.translation import ugettext_lazy as _


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return u'%s %s <%s>' % (obj.first_name, obj.last_name, obj.email)

class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"
        exclude = ['created_by']
        labels = {
            'name': _('Project name'),
            'client': _('Client'),
            'description': _('Description'),
            'created_by': _('Created by'),
            'created_at': _('Created at'),
        }

class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        exclude = []
        labels = {
            'name': _('Project name'),
            'description': _('Description'),
        }

class ProjectCloseForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['closed_description']
        exclude = []
        labels = {
            'closed_description': _('Close description'),

        }



class ProjectCreateAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"
        exclude = ['created_by']


"""
TEAM
"""


class TeamInviteForm(forms.ModelForm):
    email = forms.EmailField(label='E-mail', max_length=100, required=True)

    class Meta:
        model = Team
        fields = ['email', 'role']
        labels = {
            'role': _('Role'),
            'team_type': _('Team type'),
        }


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = "__all__"
        exclude = ['token', 'project', 'email', 'active', 'staff',
                   'team_type', 'role', 'is_removable', 'customer']
        labels = {
            'email': _('Email'),
            'role': _('Role'),
        }
        help_texts = {
            'email': _('Group to which this message belongs to'),
        }
        


# alapbol létrehoz egy időpontot
class TeamCreateWithBookForm(forms.ModelForm):
    meet_start = forms.DateTimeField(label=_('Meet start'))
    meet_end = forms.DateTimeField(label=_('Meet end'))

    class Meta:
        model = Team
        fields = ['user', 'meet_start', 'meet_end']
        exclude = ['token', 'project', 'email', 'active', 'staff',
                   'team_type', 'role', 'is_removable', 'customer']


class TeamEditForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = "__all__"
        exclude = ['token', 'project', 'user',
                   'email', 'customer', 'team_type', 'is_removable', 'staff']


"""
NOTES
"""


class NoteCreateForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = "__all__"
        exclude = ['user', 'project', 'meet', 'project_form',
                   'task', 'type', 'lawyer_mode', 'visible']
        #exclude = ['user', 'project', 'meet', 'task', 'type', 'lawyer_mode']


class NoteEditForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = "__all__"
        exclude = ['user', 'project', 'meet', 'task',
                   'type', 'project_form', 'lawyer_mode']


class NoteTaskCreateForm(forms.ModelForm):
    #private = forms.BooleanField(label='This message only show me. Private mode!', required=False)
    #visible = forms.BooleanField(label='Visible this note?', initial=True, required=False)
    class Meta:
        model = Note
        fields = "__all__"
        exclude = ['task', 'user', 'project', 'meet', 'project_form',
                   'type', 'lawyer_mode', 'private', 'visible']


class NoteMeetCreateForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = "__all__"
        exclude = ['task', 'user', 'project', 'meet',
                   'type', 'project_form', 'lawyer_mode']


class NoteFormCreateForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = "__all__"
        exclude = ['task', 'user', 'project', 'meet',
                   'type', 'project_form', 'lawyer_mode']


"""
MEET
"""


class MeetCreateForm(forms.ModelForm):
    invite_email = forms.EmailField(label='Invite email', required=False)
    class Meta:
        model = Meet
        fields = "__all__"
        exclude = ['from_user', 'project', 'lawyer_mode', 'url', 'google_calendar_id']

class MeetInviteForm(forms.ModelForm):
    class Meta:
        model = Meet
        fields = ['to_user']
        exclude = []

class MeetEditForm(forms.ModelForm):
    class Meta:
        model = Meet
        fields = ['to_user']
        exclude = []


"""
TASK
"""


class TaskCreateForm(forms.ModelForm):
    invite_email = forms.EmailField(label='Invite email', required=False)
    class Meta:
        model = Task
        fields = "__all__"
        exclude = ['from_user', 'project',
                   'lawyer_mode', 'status', 'responsible_user', 'archived']
        

class TaskEditForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"
        exclude = ['responsible_user', 'from_user', 'project', 'start_date', 'due_date',
                   'description', 'name', 'lawyer_mode', 'archived']

class TaskResponsibleForm(forms.ModelForm):
    
    class Meta:
        model = Task
        fields = ['responsible_user']
        """
        field_classes = {
            'responsible_user': UserModelChoiceField
        }
        """


  

"""
DOCUMENT
"""

class DocumentCreateForm(forms.Form):
    documents = DocumentDefault.objects.all()
    default_document = forms.ModelChoiceField(queryset=documents, label=_('Clone this document'))



class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['content']



"""
MESSSAGE
"""


class MessageCreateForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(
        attrs={'id': 'default-textarea', 'class': 'form-control form-control-simple no-resize', 'rows': '1', 'placeholder': _('Type your message...')}), label=False, required=True)

    class Meta:
        model = Message
        fields = ['content']
        exclude = ['user', 'project', 'lawyer_mode']


"""
FILE
"""


class FileCreateForm(forms.ModelForm):
    project_file = forms.FileField(label=_('Project file'))

    class Meta:
        model = File
        fields = "__all__"
        exclude = ['uploaded_by', 'project', 'note', 'meet', 'message', 'project_form',
                   'task', 'file_type', 'meet_record_url', 'lawyer_mode', 'archived', 'is_relase']
        labels = {
            'description': _('Description'),
            'name': _('Name'),
        }


class FileEditForm(forms.ModelForm):
    file_type = forms.CharField(disabled=True, label=_('File type'))

    class Meta:
        model = File
        fields = "__all__"
        exclude = ['uploaded_by', 'project', 'note', 'meet', 'message', 'project_form',
                   'task', 'meet_record_url', 'project_file', 'lawyer_mode', 'archived']
        readonly_fields = ('file_type')
        labels = {
            'description': _('Description'),
            'name': _('Name'),
            'archived': _('Archived'),
            'is_relase': _('Is relase?')
        }


"""
FORM
"""
class CreateForm(forms.ModelForm):
    multiple = forms.IntegerField(label=_('How many time duplicate this form?'))
    default_form = forms.ModelChoiceField(queryset=ProjectFormDefault.objects.filter(multiple=True))
    def __init__(self, *args, **kwargs):
        product_id = kwargs.pop('product_id', None)
        super(CreateForm, self).__init__(*args, **kwargs)

        if product_id:
            self.fields['default_form'].queryset = ProjectFormDefault.objects.filter(product=product_id, multiple=True)


    class Meta:
        model = ProjectForm
        fields = ['default_form','multiple']


class EditForm(forms.ModelForm):
    
    class Meta:
        model = ProjectForm
        fields = ['name', 'draft']

class EditParticipantForm(forms.ModelForm):
    invite_email = forms.EmailField(label='Invite email', required=False)
    class Meta:
        model = ProjectForm
        fields = ['to_user', 'invite_email']


class EditResponsibleForm(forms.ModelForm):
    """
    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team', None)
        super(EditResponsibleForm, self).__init__(*args, **kwargs)

        if team:
            self.fields['responsible_user'].queryset = team
    """
    #responsible_user = forms.ModelChoiceField(queryset=Team.objects.all(), to_field_name = 'user', empty_label="Select Gender")
    class Meta:
        model = ProjectForm
        fields = ['responsible_user']

 

class DuplicateForm(forms.ModelForm):
    multiple_number = forms.IntegerField(label=_('How many time duplicate this form?'))
    class Meta:
        model = ProjectForm
        fields = ['multiple_number']