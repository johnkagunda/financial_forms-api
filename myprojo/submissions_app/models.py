from django.db import models
from forms_app.models import Form
from fields_app.models import Field


class Submission(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.CharField(max_length=255, blank=True)  # Could be email or user ID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.id} for {self.form.name}"


class FieldResponse(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="responses")
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.FloatField(blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)
    value_json = models.JSONField(blank=True, null=True)  # For arrays/multiple choices

    def get_value(self):
        """Dynamic value getter based on field type"""
        if self.field.field_type == "text":
            return self.value_text
        elif self.field.field_type == "number":
            return self.value_number
        elif self.field.field_type == "date":
            return self.value_date
        elif self.field.field_type == "checkbox":
            return self.value_boolean
        elif self.field.field_type in ["dropdown", "file"]:
            return self.value_json
        return None

    def __str__(self):
        return f"Response to {self.field.label} (Submission {self.submission.id})"


class UploadedFile(models.Model):
    response = models.ForeignKey(FieldResponse, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message[:50]
