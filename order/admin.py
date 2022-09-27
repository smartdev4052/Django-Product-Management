from django.contrib import admin
from order.models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ['client', 'product','price','paid', 'active']

admin.site.register(Order, OrderAdmin)
