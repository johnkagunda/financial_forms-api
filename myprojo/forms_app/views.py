from rest_framework import viewsets
from .models import Form
from .serializers import FormSerializer

class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.filter(is_active=True).prefetch_related('fields')
    serializer_class = FormSerializer