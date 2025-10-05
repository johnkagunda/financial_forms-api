from rest_framework import viewsets
from .models import Field
from .serializers import FieldSerializer

class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    
    def get_queryset(self):
        queryset = Field.objects.all()
        form_id = self.request.query_params.get('form_id')
        if form_id:
            queryset = queryset.filter(form_id=form_id)
        return queryset