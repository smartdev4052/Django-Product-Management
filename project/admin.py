from django.contrib import admin
from project.models import Activity, Document,DocumentDefault, Invite, Meet, Message, Note, Project, ProjectForm, ProjectFormDefault, Task, TaskDefault, Team, File, TeamType
from django.db import models
from django_json_widget.widgets import JSONEditorWidget


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'order_number', 'responsible_user', 'archived', 'created_at']


class TeamAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'project',
                    'role', 'active', 'is_removable', 'token', 'created_at']


class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'description', 'project',
                    'is_read', 'lawyer_mode', 'created_at']


class InviteAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'invite_email', 'project',
                    'meet_start', 'meet_end','is_read', 'create_date']

class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_user', 'responsible_user', 'project', 'status',
                    'start_date', 'due_date','archived', 'created_at']


class NoteAdmin(admin.ModelAdmin):
    list_display = ['content', 'user', 'private', 'visible', 'type', 'lawyer_mode', 'created_at']

class MeetAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_user', 'project', 'meet_start',
                    'meet_end', 'google_calendar_id','url', 'created_at']


class FileAdmin(admin.ModelAdmin):
    list_display = ['name', 'project_file', 'is_relase', 'project', 'uploaded_by',
                    'lawyer_mode', 'file_type','archived', 'created_at']

class MessageAdmin(admin.ModelAdmin):
    list_display = ['content', 'user','project', 'url', 'lawyer_mode', 'created_at']



"""
@admin.register(ProjectForm)
class ProjectFormAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }



@admin.register(ProjectFormDefault)
class ProjectFormDefaultAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }
"""

admin.site.register(Project, ProjectAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Meet, MeetAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(TeamType)
admin.site.register(TaskDefault)
admin.site.register(ProjectForm)
admin.site.register(ProjectFormDefault)
admin.site.register(Document)
admin.site.register(DocumentDefault)
