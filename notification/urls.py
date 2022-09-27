from django.urls import path
from . import views

app_name = 'notification'


urlpatterns = [
    path('', views.notification_index_view, name='notification_index'),
    path('<int:id>', views.notification_detail_view, name='notification_detail')
    #path('create/', views.notification_create_view, name='notification_create'),
]
