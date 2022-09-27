from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.account_index_view, name='account_index'),
    path('edit', views.account_edit_view, name='account_edit'),
    path('template', views.email_template, name='email_template'),
    path('email', views.email_test, name='email_test'),
    
    #path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]