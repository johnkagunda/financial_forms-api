from django.contrib import admin
from .models import Form

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']