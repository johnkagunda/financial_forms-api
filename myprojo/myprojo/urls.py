from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms_app.views import FormViewSet
from fields_app.views import FieldViewSet
from submissions_app.views import SubmissionViewSet, NotificationViewSet, FormResponsesViewSet, FieldResponsesViewSet

router = DefaultRouter()
router.register(r"forms", FormViewSet)
router.register(r"fields", FieldViewSet)
router.register(r"submissions", SubmissionViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"form-responses", FormResponsesViewSet, basename="form-responses")  # New endpoint for response display
router.register(r"field-responses", FieldResponsesViewSet, basename="field-responses")  # API root endpoint for client responses

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
