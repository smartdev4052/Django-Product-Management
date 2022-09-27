from django.contrib import admin
from .models import Category, Product, Tax, Currency

#register
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'available', 'created']
    list_filter = ['available', 'created', 'updated']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name']