from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime, timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Submission, Notification, FieldResponse
from .serializers import (
    SubmissionSerializer, NotificationSerializer, DetailedSubmissionSerializer,
    FormResponsesSummarySerializer, DetailedFieldResponseSerializer
)
from forms_app.models import Form
from fields_app.models import Field

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all().select_related('form').prefetch_related(
        'responses__field', 'responses__files'
    )
    serializer_class = SubmissionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['submitted_by', 'form__name']
    ordering_fields = ['created_at', 'submitted_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return detailed serializer for list/retrieve actions"""
        if self.action in ['list', 'retrieve']:
            return DetailedSubmissionSerializer
        return SubmissionSerializer
    
    def get_queryset(self):
        """Apply manual filtering to queryset"""
        queryset = super().get_queryset()
        
        # Manual filtering since we don't have django-filter
        form_id = self.request.query_params.get('form')
        if form_id:
            queryset = queryset.filter(form_id=form_id)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        submitted_by = self.request.query_params.get('submitted_by')
        if submitted_by:
            queryset = queryset.filter(submitted_by__icontains=submitted_by)
        
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(submitted_at=timezone.now(), status="submitted")

        # Create a Notification record
        try:
            Notification.objects.create(
                message=f"Form '{submission.form.name}' answered by {submission.submitted_by or 'Anonymous'} (Submission {submission.id})"
            )
        except Exception:
            pass

        # Broadcast notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": {
                    "id": submission.id,
                    "message": f"New submission received",
                    "submission_id": submission.id,
                    "form_name": submission.form.name,
                    "submitted_by": submission.submitted_by or "Anonymous",
                    "created_at": str(submission.submitted_at),
                }
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def by_form(self, request):
        """Get submissions grouped by form"""
        form_id = request.query_params.get('form_id')
        if not form_id:
            return Response({'error': 'form_id parameter required'}, status=400)
        
        submissions = self.get_queryset().filter(form_id=form_id)
        
        # Apply additional filters
        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            submissions = submissions.filter(created_at__gte=date_from)
        if date_to:
            submissions = submissions.filter(created_at__lte=date_to)
        
        serializer = DetailedSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent submissions (last 7 days by default)"""
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        submissions = self.get_queryset().filter(created_at__gte=since)
        serializer = DetailedSubmissionSerializer(submissions, many=True)
        return Response({
            'period': f'Last {days} days',
            'count': submissions.count(),
            'submissions': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get submission statistics"""
        total = self.get_queryset().count()
        by_status = self.get_queryset().values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        recent_count = self.get_queryset().filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_submissions': total,
            'recent_submissions': recent_count,
            'by_status': list(by_status),
            'by_form': list(
                self.get_queryset().values(
                    'form__id', 'form__name'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')
            )
        })


class FormResponsesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for displaying all form responses with comprehensive data and accepting submissions"""
    queryset = Form.objects.all().prefetch_related(
        'fields', 'submissions__responses__field', 'submissions__responses__files'
    )
    serializer_class = FormResponsesSummarySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit answers for a specific form.
        Accepts flexible input formats and creates a Submission + FieldResponses.

        Payload examples:
        1) answers as a mapping of field labels to values
           {
             "submitted_by": "user@example.com",
             "answers": { "Full Name": "John", "Age": 30, "Birthday": "2024-01-01" }
           }

        2) answers_list as an array using field_id or field_label
           {
             "submitted_by": "user@example.com",
             "answers_list": [
               {"field_id": 12, "value": "John"},
               {"field_label": "Age", "value": 30}
             ]
           }
        """
        from django.db import transaction

        form = self.get_object()
        submitted_by = request.data.get('submitted_by', '')
        ip_address = self._get_client_ip(request)

        # Build a map of fields by id and by tolerant label keys for quick lookup
        fields = list(form.fields.all())
        fields_by_id = {f.id: f for f in fields}
        fields_by_key = {}
        for f in fields:
            label_str = str(f.label)
            candidates = {
                label_str,
                label_str.strip(),
                label_str.strip().lower(),
                slugify(label_str),
            }
            for c in candidates:
                fields_by_key[c] = f

        # Normalize input into a list of (field, value)
        normalized = []
        errors = []

        if 'answers' in request.data and isinstance(request.data['answers'], dict):
            for key, value in request.data['answers'].items():
                key_str = str(key)
                key_candidates = [
                    key_str,
                    key_str.strip(),
                    key_str.strip().lower(),
                    slugify(key_str),
                ]
                field = None
                for kc in key_candidates:
                    field = fields_by_key.get(kc)
                    if field:
                        break
                if not field:
                    field = fields_by_id.get(self._safe_int(key))
                if not field:
                    errors.append(f"Unknown field '{key}' for this form")
                    continue
                normalized.append((field, value))
        elif 'answers_list' in request.data and isinstance(request.data['answers_list'], list):
            for item in request.data['answers_list']:
                fid = item.get('field_id')
                flabel = item.get('field_label')
                value = item.get('value')
                field = None
                if fid is not None:
                    field = fields_by_id.get(self._safe_int(fid))
                if not field and flabel is not None:
                    flabel_str = str(flabel)
                    for kc in [
                        flabel_str,
                        flabel_str.strip(),
                        flabel_str.strip().lower(),
                        slugify(flabel_str),
                    ]:
                        field = fields_by_key.get(kc)
                        if field:
                            break
                if not field:
                    errors.append(f"Unknown field reference in {item}")
                    continue
                normalized.append((field, value))
        else:
            return Response({
                'error': 'Provide answers as either an object in "answers" or an array in "answers_list".'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check required fields are present
        missing_required = [f.label for f in fields if f.required and f not in [fld for (fld, _) in normalized]]
        if missing_required:
            return Response({
                'error': 'Missing required fields',
                'missing_fields': missing_required,
                'other_errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create submission and responses atomically
        with transaction.atomic():
            submission = Submission.objects.create(
                form=form,
                submitted_by=submitted_by,
                status='submitted',
                submitted_at=timezone.now(),
                ip_address=ip_address,
            )

            summary = {}
            for field, value in normalized:
                fr_kwargs = {
                    'submission': submission,
                    'field': field,
                    'value_text': None,
                    'value_number': None,
                    'value_date': None,
                    'value_boolean': None,
                    'value_json': None,
                }

                # Coerce value based on field type
                try:
                    if field.field_type == 'text':
                        fr_kwargs['value_text'] = str(value) if value is not None else None
                        summary[field.label] = fr_kwargs['value_text']
                    elif field.field_type == 'number':
                        fr_kwargs['value_number'] = float(value) if value not in (None, '') else None
                        summary[field.label] = fr_kwargs['value_number']
                    elif field.field_type == 'date':
                        # Accept YYYY-MM-DD
                        if value:
                            fr_kwargs['value_date'] = datetime.strptime(str(value), '%Y-%m-%d').date()
                        summary[field.label] = str(fr_kwargs['value_date']) if fr_kwargs['value_date'] else None
                    elif field.field_type == 'checkbox':
                        if isinstance(value, str):
                            v_lower = value.strip().lower()
                            val = v_lower in ['true', '1', 'yes', 'y']
                        else:
                            val = bool(value)
                        fr_kwargs['value_boolean'] = val
                        summary[field.label] = fr_kwargs['value_boolean']
                    elif field.field_type in ['dropdown', 'file']:
                        # Store raw value(s) as JSON; allow string or list
                        fr_kwargs['value_json'] = value
                        summary[field.label] = fr_kwargs['value_json']
                    else:
                        # Unknown type: store as text
                        fr_kwargs['value_text'] = str(value) if value is not None else None
                        summary[field.label] = fr_kwargs['value_text']
                except Exception as e:
                    errors.append(f"Failed to parse value for '{field.label}': {e}")
                    continue

                FieldResponse.objects.create(**fr_kwargs)

        # Create a Notification record
        try:
            Notification.objects.create(
                message=f"Form '{form.name}' answered by {submitted_by or 'Anonymous'} (Submission {submission.id})"
            )
        except Exception:
            pass

        # Broadcast notification (reuse existing mechanism)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": {
                    "id": submission.id,
                    "message": f"New submission received",
                    "submission_id": submission.id,
                    "form_name": form.name,
                    "submitted_by": submitted_by or "Anonymous",
                    "created_at": str(submission.submitted_at),
                }
            }
        )

        return Response({
            'submission_id': submission.id,
            'form_id': form.id,
            'submitted_by': submitted_by,
            'errors': errors,
            'answers': summary
        }, status=status.HTTP_201_CREATED)

    def _safe_int(self, v):
        try:
            return int(v)
        except Exception:
            return None

    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        queryset = super().get_queryset()
        
        # Manual filtering for form status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        """Get all responses for a specific form"""
        form = self.get_object()
        submissions = form.submissions.all().select_related('form').prefetch_related(
            'responses__field', 'responses__files'
        )
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            submissions = submissions.filter(created_at__gte=date_from)
        if date_to:
            submissions = submissions.filter(created_at__lte=date_to)
        
        submitted_by = request.query_params.get('submitted_by')
        if submitted_by:
            submissions = submissions.filter(submitted_by__icontains=submitted_by)
        
        serializer = DetailedSubmissionSerializer(submissions, many=True)
        return Response({
            'form': {
                'id': form.id,
                'name': form.name,
                'description': form.description
            },
            'total_submissions': submissions.count(),
            'submissions': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get detailed analytics for a specific form"""
        form = self.get_object()
        submissions = form.submissions.all()
        
        # Basic statistics
        total_submissions = submissions.count()
        status_breakdown = submissions.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Time-based analytics
        last_30_days = timezone.now() - timedelta(days=30)
        recent_submissions = submissions.filter(created_at__gte=last_30_days).count()
        
        # Field response analytics
        field_analytics = []
        for field in form.fields.all():
            responses = FieldResponse.objects.filter(
                submission__form=form, field=field
            )
            
            field_stat = {
                'field_id': field.id,
                'field_label': field.label,
                'field_type': field.field_type,
                'required': field.required,
                'total_responses': responses.count(),
                'response_rate': (responses.count() / total_submissions * 100) if total_submissions > 0 else 0,
            }
            
            # Type-specific analytics
            if field.field_type == 'dropdown' and field.options:
                option_counts = {}
                for response in responses:
                    value = response.get_value()
                    if value:
                        option_counts[str(value)] = option_counts.get(str(value), 0) + 1
                field_stat['option_breakdown'] = option_counts
            
            elif field.field_type == 'checkbox':
                true_count = responses.filter(value_boolean=True).count()
                false_count = responses.filter(value_boolean=False).count()
                field_stat['checkbox_breakdown'] = {
                    'true': true_count,
                    'false': false_count
                }
            
            field_analytics.append(field_stat)
        
        return Response({
            'form': {
                'id': form.id,
                'name': form.name,
                'total_fields': form.fields.count()
            },
            'submission_analytics': {
                'total_submissions': total_submissions,
                'recent_submissions': recent_submissions,
                'status_breakdown': list(status_breakdown),
                'average_completion_rate': sum(
                    field['response_rate'] for field in field_analytics
                ) / len(field_analytics) if field_analytics else 0
            },
            'field_analytics': field_analytics
        })
    
    @action(detail=False, methods=['get'])
    def all_responses(self, request):
        """Get all responses across all forms"""
        all_submissions = Submission.objects.all().select_related('form').prefetch_related(
            'responses__field', 'responses__files'
        )
        
        # Apply global filters
        form_id = request.query_params.get('form_id')
        if form_id:
            all_submissions = all_submissions.filter(form_id=form_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            all_submissions = all_submissions.filter(status=status_filter)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            all_submissions = all_submissions.filter(created_at__gte=date_from)
        if date_to:
            all_submissions = all_submissions.filter(created_at__lte=date_to)
        
        # Pagination
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = all_submissions.count()
        paginated_submissions = all_submissions[start:end]
        
        serializer = DetailedSubmissionSerializer(paginated_submissions, many=True)
        
        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'submissions': serializer.data
        })


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer


class FieldResponsesViewSet(viewsets.ViewSet):
    """
    API root endpoint for client field responses corresponding to admin-created forms.
    - GET /api/field-responses/    -> list submissions with answers mapping
    - POST /api/field-responses/   -> create a submission with answers
    """

    def _safe_int(self, v):
        try:
            return int(v)
        except Exception:
            return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def list(self, request):
        qs = Submission.objects.all().select_related('form').prefetch_related(
            'responses__field', 'responses__files'
        )
        # Filters
        form_id = request.query_params.get('form') or request.query_params.get('form_id')
        if form_id:
            qs = qs.filter(form_id=form_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        submitted_by = request.query_params.get('submitted_by')
        if submitted_by:
            qs = qs.filter(submitted_by__icontains=submitted_by)
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        # Pagination
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        total_count = qs.count()
        page_items = qs.order_by('-created_at')[start:end]

        items = []
        for sub in page_items:
            answers = {}
            resp_qs = sub.responses.all()
            for resp in resp_qs:
                answers[resp.field.label] = resp.get_value()
            items.append({
                'submission_id': sub.id,
                'form_id': sub.form_id,
                'form_name': sub.form.name,
                'submitted_by': sub.submitted_by,
                'status': sub.status,
                'submitted_at': sub.submitted_at,
                'created_at': sub.created_at,
                'answers': answers,
                'field_responses': DetailedFieldResponseSerializer(resp_qs, many=True).data,
            })

        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': items,
        })

    def create(self, request):
        """
        Create a submission with client answers.
        Body accepts either:
        - {
            "form_id": 1,
            "submitted_by": "user@example.com",
            "answers": { "Full Name": "John", "Age": 30 }
          }
        - {
            "form_id": 1,
            "submitted_by": "user@example.com",
            "answers_list": [ {"field_id": 12, "value": "John"}, {"field_label": "Age", "value": 30} ]
          }
        """
        form_id = request.data.get('form') or request.data.get('form_id')
        if not form_id:
            return Response({'error': 'form_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return Response({'error': f'Form {form_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        submitted_by = request.data.get('submitted_by', '')
        ip_address = self._get_client_ip(request)

        # Build tolerant field key map
        fields = list(form.fields.all())
        fields_by_id = {f.id: f for f in fields}
        fields_by_key = {}
        for f in fields:
            label_str = str(f.label)
            candidates = {
                label_str,
                label_str.strip(),
                label_str.strip().lower(),
                slugify(label_str),
            }
            for c in candidates:
                fields_by_key[c] = f

        normalized = []
        errors = []

        if 'answers' in request.data and isinstance(request.data['answers'], dict):
            for key, value in request.data['answers'].items():
                key_str = str(key)
                key_candidates = [
                    key_str,
                    key_str.strip(),
                    key_str.strip().lower(),
                    slugify(key_str),
                ]
                field = None
                for kc in key_candidates:
                    field = fields_by_key.get(kc)
                    if field:
                        break
                if not field:
                    field = fields_by_id.get(self._safe_int(key))
                if not field:
                    errors.append(f"Unknown field '{key}' for this form")
                    continue
                normalized.append((field, value))
        elif 'answers_list' in request.data and isinstance(request.data['answers_list'], list):
            for item in request.data['answers_list']:
                fid = item.get('field_id')
                flabel = item.get('field_label')
                value = item.get('value')
                field = None
                if fid is not None:
                    field = fields_by_id.get(self._safe_int(fid))
                if not field and flabel is not None:
                    flabel_str = str(flabel)
                    for kc in [
                        flabel_str,
                        flabel_str.strip(),
                        flabel_str.strip().lower(),
                        slugify(flabel_str),
                    ]:
                        field = fields_by_key.get(kc)
                        if field:
                            break
                if not field:
                    errors.append(f"Unknown field reference in {item}")
                    continue
                normalized.append((field, value))
        else:
            return Response({'error': 'Provide answers in "answers" or "answers_list"'}, status=status.HTTP_400_BAD_REQUEST)

        # Required fields validation
        missing_required = [f.label for f in fields if f.required and f not in [fld for (fld, _) in normalized]]
        if missing_required:
            return Response({
                'error': 'Missing required fields',
                'missing_fields': missing_required,
                'other_errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create submission and responses
        from django.db import transaction
        with transaction.atomic():
            submission = Submission.objects.create(
                form=form,
                submitted_by=submitted_by,
                status='submitted',
                submitted_at=timezone.now(),
                ip_address=ip_address,
            )

            summary = {}
            for field, value in normalized:
                fr_kwargs = {
                    'submission': submission,
                    'field': field,
                    'value_text': None,
                    'value_number': None,
                    'value_date': None,
                    'value_boolean': None,
                    'value_json': None,
                }
                try:
                    if field.field_type == 'text':
                        fr_kwargs['value_text'] = str(value) if value is not None else None
                        summary[field.label] = fr_kwargs['value_text']
                    elif field.field_type == 'number':
                        fr_kwargs['value_number'] = float(value) if value not in (None, '') else None
                        summary[field.label] = fr_kwargs['value_number']
                    elif field.field_type == 'date':
                        if value:
                            fr_kwargs['value_date'] = datetime.strptime(str(value), '%Y-%m-%d').date()
                        summary[field.label] = str(fr_kwargs['value_date']) if fr_kwargs['value_date'] else None
                    elif field.field_type == 'checkbox':
                        if isinstance(value, str):
                            v_lower = value.strip().lower()
                            val = v_lower in ['true', '1', 'yes', 'y']
                        else:
                            val = bool(value)
                        fr_kwargs['value_boolean'] = val
                        summary[field.label] = fr_kwargs['value_boolean']
                    elif field.field_type in ['dropdown', 'file']:
                        fr_kwargs['value_json'] = value
                        summary[field.label] = fr_kwargs['value_json']
                    else:
                        fr_kwargs['value_text'] = str(value) if value is not None else None
                        summary[field.label] = fr_kwargs['value_text']
                except Exception as e:
                    errors.append(f"Failed to parse value for '{field.label}': {e}")
                    continue
                FieldResponse.objects.create(**fr_kwargs)

        # Create a Notification record
        try:
            Notification.objects.create(
                message=f"Form '{form.name}' answered by {submitted_by or 'Anonymous'} (Submission {submission.id})"
            )
        except Exception:
            pass

        # Broadcast notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": {
                    "id": submission.id,
                    "message": f"New submission received",
                    "submission_id": submission.id,
                    "form_name": form.name,
                    "submitted_by": submitted_by or "Anonymous",
                    "created_at": str(submission.submitted_at),
                }
            }
        )

        # Serialize field responses for the created submission
        created_responses = DetailedFieldResponseSerializer(submission.responses.all(), many=True).data

        return Response({
            'submission_id': submission.id,
            'form_id': form.id,
            'submitted_by': submitted_by,
            'errors': errors,
            'answers': summary,
            'field_responses': created_responses
        }, status=status.HTTP_201_CREATED)

# Broadcast FieldResponse notifications
@receiver(post_save, sender=FieldResponse)
def broadcast_response_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": {
                    "id": instance.id,
                    "message": f"New response for Submission {instance.submission.id}",
                    "submission_id": instance.submission.id,
                    "form_name": instance.submission.form.name,
                    "submitted_by": instance.submission.submitted_by or "Anonymous",
                    # FieldResponse doesn't have created_at; use now
                    "created_at": str(timezone.now()),
                },
            },
        )
