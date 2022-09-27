from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index_view, name='index_view'),
    path('meet', views.meet_index_view, name='meet_index'),
    path('task', views.task_index_view, name='task_index'),
    path('activity', views.activity_index_view,name='activity_index'),
    path('activity/<int:id>', views.activity_detail_view,name='activity_detail'),
    path('page', views.page_index_view,name='page_index'),
    path('page/create', views.page_create_view,name='page_create'),
    path('page/edit/<slug:slug>', views.page_edit_view,name='page_edit'),
    path('page/delete/<slug:slug>', views.page_delete_view,name='page_delete'),
    path('page/<slug:slug>', views.page_detail_view,name='page_detail'),
    #for document
    path('document', views.document_index_view,name='document_index'),
    path('document/create', views.document_create_view,name='document_create'),
    path('document/<int:id>', views.document_detail_view,name='document_detail'),
    path('document/edit/<int:id>', views.document_edit_view,name='document_edit'),
    path('document/delete/<int:id>', views.document_delete_view,name='document_delete'),
    

    #mesibo
    path('mesibo', views.mesibo_view,name='mesibo'),

    #for testing
    path('calendar', views.calendar_index_view, name='calendar_index'),
    path('calendar/create', views.calendar_create_view, name='calendar_create'),

    path('calendly', views.calendly, name='calendly'),
    path('json_calendly_view', views.json_calendly_view, name='json_calendly_view'),

]
