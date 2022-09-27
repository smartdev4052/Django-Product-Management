from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    path('', views.client_index_view, name='client_index'),
    path('<int:id>', views.client_detail_view, name='client_detail'),
    path('create/', views.client_create_view, name='client_create'),
    path('edit/<int:id>', views.client_edit_view, name='client_edit'),
    path('archive/<int:id>', views.client_archive_view, name='client_archive'),
    path('delete/<int:id>', views.client_delete_view, name='client_delete'),
]
