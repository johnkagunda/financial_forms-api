from django.db import models
from forms_app.models import Form

class Field(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("dropdown", "Dropdown"),
        ("checkbox", "Checkbox"),
        ("file", "File Upload"),
    ]
    
    VALIDATION_TYPES = [
        ("none", "None"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("regex", "Custom Regex"),
        ("conditional", "Conditional"),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)  # For dropdown/checkbox options
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES, default="none")
    validation_rule = models.TextField(blank=True, null=True)  # Custom regex or conditions
    order = models.IntegerField(default=0)  # Field ordering
    conditional_logic = models.JSONField(blank=True, null=True)  # Show/hide based on other fields

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label} ({self.field_type})"