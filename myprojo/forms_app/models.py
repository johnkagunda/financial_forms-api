from django.db import models

class Form(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Form configuration
    allow_multiple_submissions = models.BooleanField(default=False)
    require_login = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name