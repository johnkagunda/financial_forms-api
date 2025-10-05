from rest_framework import serializers
from .models import Submission, FieldResponse, UploadedFile, Notification
from fields_app.models import Field
from forms_app.models import Form


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = "__all__"


class FieldResponseSerializer(serializers.ModelSerializer):
    files = UploadedFileSerializer(many=True, read_only=True)

    class Meta:
        model = FieldResponse
        fields = "__all__"


class SubmissionSerializer(serializers.ModelSerializer):
    responses = FieldResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


# Enhanced serializers for form response display
class FieldDetailSerializer(serializers.ModelSerializer):
    """Detailed field information for response display"""
    class Meta:
        model = Field
        fields = ['id', 'label', 'field_type', 'required', 'options', 'validation_type', 'order']


class DetailedFieldResponseSerializer(serializers.ModelSerializer):
    """Enhanced field response with field details and formatted value"""
    field = FieldDetailSerializer(read_only=True)
    files = UploadedFileSerializer(many=True, read_only=True)
    formatted_value = serializers.SerializerMethodField()
    
    class Meta:
        model = FieldResponse
        fields = ['id', 'field', 'formatted_value', 'files', 'value_text', 'value_number', 
                 'value_date', 'value_boolean', 'value_json']
    
    def get_formatted_value(self, obj):
        """Get the properly formatted value based on field type"""
        return obj.get_value()


class FormBasicSerializer(serializers.ModelSerializer):
    """Basic form information for response listings"""
    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'is_active', 'created_at']


class DetailedSubmissionSerializer(serializers.ModelSerializer):
    """Enhanced submission with form details and organized responses"""
    form = FormBasicSerializer(read_only=True)
    responses = DetailedFieldResponseSerializer(many=True, read_only=True)
    response_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = ['id', 'form', 'submitted_by', 'status', 'submitted_at', 'created_at', 
                 'ip_address', 'responses', 'response_count']
    
    def get_response_count(self, obj):
        """Count of responses in this submission"""
        return obj.responses.count()


class FormResponsesSummarySerializer(serializers.ModelSerializer):
    """Form with all its responses and statistics"""
    fields = FieldDetailSerializer(many=True, read_only=True)
    submissions = DetailedSubmissionSerializer(many=True, read_only=True)
    total_submissions = serializers.SerializerMethodField()
    total_responses = serializers.SerializerMethodField()
    submission_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at',
                 'allow_multiple_submissions', 'require_login', 'fields', 'submissions',
                 'total_submissions', 'total_responses', 'submission_stats']
    
    def get_total_submissions(self, obj):
        """Total number of submissions for this form"""
        return obj.submissions.count()
    
    def get_total_responses(self, obj):
        """Total number of field responses across all submissions"""
        return FieldResponse.objects.filter(submission__form=obj).count()
    
    def get_submission_stats(self, obj):
        """Statistics about submissions"""
        submissions = obj.submissions.all()
        stats = {
            'total': submissions.count(),
            'by_status': {}
        }
        
        for status_key, status_label in Submission.STATUS_CHOICES:
            count = submissions.filter(status=status_key).count()
            stats['by_status'][status_key] = {
                'count': count,
                'label': status_label
            }
        
        return stats
