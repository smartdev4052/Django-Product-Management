from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.shop_index_view, name='shop_index'),
    path('<slug:slug>', views.shop_detail_view, name='shop_detail'),
    path('category', views.shop_category_view, name='shop_category'),
    path('category/<slug:slug>', views.shop_by_category_view, name='shop_by_category'),
    path('product', views.product_index_view, name='product_index'),
    path('product/<int:id>', views.product_detail_view, name='product_detail'),
    path('product/create', views.product_create_view, name='product_create'),
    path('product/edit/<int:id>', views.product_edit_view, name='product_edit'),
    path('product/delete/<int:id>', views.product_delete_view, name='product_delete'),
    
]

