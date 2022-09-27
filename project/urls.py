from django.urls import path
from . import views

app_name = 'project'

urlpatterns = [
    path('', views.project_index_view, name='project_index'),
    path('create/<client_id>/<product_id>/<order_id>',
         views.project_create_view, name='project_create'),
    path('create/admin', views.project_create_admin_view,
         name='project_create_admin'),
    path('<int:id>', views.project_detail_view, name='project_detail'),
    path('edit/<int:project_id>', views.project_edit_view, name='project_edit'),
    path('close/<int:project_id>', views.project_close_view, name='project_close'),
    path('archive/<int:project_id>', views.project_archive_view, name='project_archive'),
    path('unarchive/<int:project_id>', views.project_unarchive_view, name='project_unarchive'),


    # Team
    path('<int:project_id>/team', views.project_team_index_view,
         name='project_team_index'),
    path('<int:project_id>/team/create',
         views.project_team_create_view, name='project_team_create'),
    path('<int:project_id>/team-book/create',
         views.project_team_book_create_view, name='project_team_book_create'),
    path('<int:project_id>/team/edit/<int:id>',
         views.project_team_edit_view, name='project_team_edit'),
    path('<int:project_id>/project_team_invite',
         views.project_team_invite_view, name='project_team_invite'),
     path('<int:project_id>/team/invite/delete/<int:id>',
         views.project_team_invite_delete_view, name='project_team_invite_delete'),

     # Document
     
    path('<int:project_id>/document', views.project_document_index_view,
         name='project_document_index'),
    path('<int:project_id>/document/create',
         views.project_document_create_view, name='project_document_create'),
     path('<int:project_id>/document/detail/<int:id>',
         views.project_document_detail_view, name='project_document_detail'),
    path('<int:project_id>/document/edit/<int:id>',
         views.project_document_edit_view, name='project_document_edit'),
     path('<int:project_id>/document/pdf/generate/<int:id>',
         views.GeneratePdf.as_view(), name='project_document_pdf_generate'),
     path('<int:project_id>/document/delete/<int:id>',
         views.project_document_delete_view, name='project_document_delete'),

     

    # Note
    path('<int:project_id>/note', views.project_note_index_view,
         name='project_note_index'),
    path('<int:project_id>/note/create',
         views.project_note_create_view, name='project_note_create'),
    path('<int:project_id>/note/edit/<int:id>',
         views.project_note_edit_view, name='project_note_edit'),
    path('<int:project_id>/note/<int:id>/file/create',
         views.project_note_create_file_view, name='project_note_create_file'),

    # Meet
    path('<int:project_id>/meet', views.project_meet_index_view,
         name='project_meet_index'),
    path('<int:project_id>/meet/create',
         views.project_meet_create_view, name='project_meet_create'),
    path('<int:project_id>/meet/<int:id>',
         views.project_meet_detail_view, name='project_meet_detail'),
    path('<int:project_id>/meet/<int:id>/file/create',
         views.project_meet_create_file_view, name='project_meet_create_file'),
     path('<int:project_id>/meet/<int:id>/edit',
         views.project_meet_edit_view, name='project_meet_edit'),
     path('<int:project_id>/meet/<int:id>/invite',
         views.project_meet_invite_view, name='project_meet_invite'),
    path('<int:project_id>/meet/<int:id>/note/create',
         views.project_note_meet_create_view, name='project_note_meet_create'),
     path('<int:project_id>/meet/delete/<int:id>',
         views.project_meet_delete_view, name='project_meet_delete'),

         
    # Task
    path('<int:project_id>/task', views.project_task_index_view,
         name='project_task_index'),
    path('<int:project_id>/task/<int:id>',
         views.project_task_detail_view, name='project_task_detail'),
    path('<int:project_id>/task/create',
         views.project_task_create_view, name='project_task_create'),
    path('<int:project_id>/task/edit/<int:id>',
         views.project_task_edit_view, name='project_task_edit'),
     path('<int:project_id>/task/responsible/<int:id>',
         views.project_task_responsible_view, name='project_task_responsible'),
    path('<int:project_id>/task/<int:id>/file/create',
         views.project_task_create_file_view, name='project_task_create_file'),
    path('<int:project_id>/task/<int:id>/note/create',
         views.project_note_task_create_view, name='project_note_task_create'),
    path('<int:project_id>/task/archive/<int:id>',
         views.project_task_archive_view, name='project_task_archive'),
     path('<int:project_id>/task/unarchive/<int:id>',
         views.project_task_unarchive_view, name='project_task_unarchive'),

    # Message
    path('<int:project_id>/message', views.project_message_index_view,
         name='project_message_index'),
    path('<int:project_id>/message/users',
         views.project_message_users_view, name='project_message_users'),
    path('<int:project_id>/message/file',
         views.project_message_files_view, name='project_message_files'),

    # File
    path('<int:project_id>/file', views.project_file_index_view,
         name='project_file_index'),
    path('<int:project_id>/file/<int:id>',
         views.project_file_detail_view, name='project_file_detail'),
    path('<int:project_id>/file/create',
         views.project_file_create_view, name='project_file_create'),
    path('<int:project_id>/file/edit/<int:id>',
         views.project_file_edit_view, name='project_file_edit'),
    path('<int:project_id>/file/archive/<int:id>',
         views.project_file_archive_view, name='project_file_archive'),
     path('<int:project_id>/file/unarchive/<int:id>',
         views.project_file_unarchive_view, name='project_file_unarchive'),
    path('<int:project_id>/file/delete/<int:id>',
         views.project_file_delete_view, name='project_file_delete'),


    # Forms
     path('<int:project_id>/form', views.project_form_index_view, name='project_form_index'),
     path('<int:project_id>/form/<int:id>', views.project_form_detail_view, name='project_form_detail'),
     path('<int:project_id>/form/create', views.project_form_create_view, name='project_form_create'),
     # Add users and edit
     path('<int:project_id>/form/duplicate/<int:id>', views.project_form_duplicate_view, name='project_form_duplicate'),
     path('<int:project_id>/form/responsible/<int:id>', views.project_form_responsible_view, name='project_form_responsible'),

    path('<int:project_id>/form/edit/<int:id>', views.project_form_edit_view, name='project_form_edit'),
    path('<int:project_id>/form/edit/participant/<int:id>', views.project_form_edit_participant_view, name='project_form_edit_participant'),
    
    path('forms', views.forms_index_view, name='forms_index'),
    path('<int:project_id>/form/<int:id>/file/create', views.project_form_create_file_view, name='project_form_create_file'),
    path('<int:project_id>/form/<int:id>/note/create', views.project_note_form_create_view, name='project_note_form_create'),

    # Activity
    path('<int:project_id>/activity', views.project_activity_index_view, name='project_activity_index'),
    path('<int:project_id>/lawyer/activity', views.project_lawyer_activity_index_view, name='project_lawyer_activity_index'),

    # Invite
    path('invite', views.invite_index_view, name='invite_index'),
    path('invite/accept/<int:project_id>', views.invite_accept_view, name='invite_accept'),
    path('invite/decline/<int:project_id>', views.invite_decline_view, name='invite_decline'),

    # Lawyer ----------------------------------------------------------------------------------------------

    # Lawyer Overview
    path('<int:project_id>/lawyer', views.project_lawyer_index_view,
         name='project_lawyer_index'),

    # Lawyer - Note
    path('<int:project_id>/lawyer/note',
         views.project_lawyer_note_index_view, name='project_lawyer_note_index'),
    path('<int:project_id>/lawyer/note/create',
         views.project_lawyer_note_create_view, name='project_lawyer_note_create'),
    #path('<int:project_id>/lawyer/note/edit/<int:id>', views.project_lawyer_note_edit_view, name='project_lawyer_note_edit'),
    path('<int:project_id>/lawyer/note/<int:id>/file/create',
         views.project_lawyer_note_create_file_view, name='project_lawyer_note_create_file'),

    # Lawyer - Task
    path('<int:project_id>/lawyer/task',
         views.project_lawyer_task_index_view, name='project_lawyer_task_index'),
    path('<int:project_id>/lawyer/task/<int:id>',
         views.project_lawyer_task_detail_view, name='project_lawyer_task_detail'),
    path('<int:project_id>/lawyer/task/create',
         views.project_lawyer_task_create_view, name='project_lawyer_task_create'),
    path('<int:project_id>/lawyer/task/edit/<int:id>',
         views.project_lawyer_task_edit_view, name='project_lawyer_task_edit'),
    path('<int:project_id>/lawyer/task/<int:id>/file/create',
         views.project_lawyer_task_create_file_view, name='project_lawyer_task_create_file'),
    path('<int:project_id>/lawyer/task/<int:id>/note/create',
         views.project_lawyer_note_task_create_view, name='project_lawyer_note_task_create'),
    path('<int:project_id>/lawyer/task/archive/<int:id>',
         views.project_lawyer_task_archive_view, name='project_lawyer_task_archive'),

    # Lawyer - Message
    path('<int:project_id>/lawyer/message',
         views.project_lawyer_message_index_view, name='project_lawyer_message_index'),
    path('<int:project_id>/lawyer/message/users',
         views.project_lawyer_message_users_view, name='project_lawyer_message_users'),
    path('<int:project_id>/lawyer/message/file',
         views.project_lawyer_message_files_view, name='project_lawyer_message_files'),

    # File
    path('<int:project_id>/lawyer/file',
         views.project_lawyer_file_index_view, name='project_lawyer_file_index'),
    path('<int:project_id>/lawyer/file/<int:id>',
         views.project_lawyer_file_detail_view, name='project_lawyer_file_detail'),
    path('<int:project_id>/lawyer/file/create',
         views.project_lawyer_file_create_view, name='project_lawyer_file_create'),
    path('<int:project_id>/lawyer/file/edit/<int:id>',
         views.project_lawyer_file_edit_view, name='project_lawyer_file_edit'),
    path('<int:project_id>/lawyer/file/archive/<int:id>',
         views.project_lawyer_file_archive_view, name='project_lawyer_file_archive'),
    #path('<int:project_id>/file/delete/<int:id>', views.project_file_delete_view, name='project_file_delete'),


    # AJAX
    path('form/save', views.form_save_ajax, name='form_save_ajax'),
    path('calendar_by_user', views.calendar_by_user, name='calendar_by_user'),
    path('nextmeet', views.project_next_meet_ajax,
         name='project_next_meet_ajax'),
     path('project_document_by_form', views.project_document_by_form, name='project_document_by_form'),
     path('project/document/clone', views.project_default_document_clone_view, name='project_default_document_clone'),



]
