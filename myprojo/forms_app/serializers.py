from rest_framework import serializers
from .models import Form
from fields_app.serializers import FieldSerializer

class FormSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Form
        fields = '__all__'