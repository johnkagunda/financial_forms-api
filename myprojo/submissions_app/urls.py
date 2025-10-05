from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('test/', TemplateView.as_view(template_name='notifications_test.html'), name='test-notifications'),
    path('admin-panel/', TemplateView.as_view(template_name='admin_panel.html'), name='admin-panel'),
    path('submission-form/', TemplateView.as_view(template_name='submission_form.html'), name='submission-form'),
]
