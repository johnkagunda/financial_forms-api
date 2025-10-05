from django.contrib import admin
from .models import Field

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'field_type', 'form', 'required', 'order']
    list_filter = ['field_type', 'required', 'form']
    search_fields = ['label', 'form__name']