from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('', views.order_index_view, name='order_index'),
    path('create/<product_id>', views.order_create_view, name='order_create'),
    path('<int:id>', views.order_detail_view, name='order_detail'),
    path('edit/<int:id>', views.order_edit_view, name='order_edit'),
    path('delete/<id>', views.order_delete_view, name='order_delete'),

    path('ajax/client', views.order_ajax_client_view, name='order_ajax_client'),
    path('ajax/json_slot', views.json_slot, name='json_slot'),

    path('widget/<product_id>', views.order_widget_view, name='order_widget'),
]
