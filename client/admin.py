from django.contrib import admin
from .models import Client, City, Country, State
from import_export.admin import ImportExportModelAdmin

#register
admin.site.register(Client)
#admin.site.register(City)
admin.site.register(Country)
#admin.site.register(State)
#class CategoryAdmin(admin.ModelAdmin):
    #list_display = ['name', 'slug']
    #prepopulated_fields = {'slug': ('name',)}

@admin.register(State)
class StateAdmin(ImportExportModelAdmin):
    ordering = ['id']
    search_fields = ['name']

@admin.register(City)
class CityOptionsAdmin(ImportExportModelAdmin):
    ordering = ['id']
    search_fields = ['name']
