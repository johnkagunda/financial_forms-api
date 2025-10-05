from django.urls import path
from . import views

urlpatterns = [
    # Get form details with all its fields
    path('forms/<int:id>/', views.FormDetailView.as_view(), name='form-detail'),
    
    # Get only fields for a specific form
    path('forms/<int:form_id>/fields/', views.FormFieldsView.as_view(), name='form-fields'),
    
    # Alternative endpoint to get form with fields
    path('forms/<int:form_id>/with-fields/', views.form_with_fields, name='form-with-fields'),
]