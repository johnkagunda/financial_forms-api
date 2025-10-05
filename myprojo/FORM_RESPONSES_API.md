# Form Responses API Documentation

This document describes the comprehensive API endpoints for displaying all responses from dynamically created form fields in your Google Forms-like API.

## Overview

The API provides multiple endpoints to view, filter, and analyze form responses:

1. **Enhanced Submissions API** - View individual submissions with detailed response data
2. **Form Responses API** - View all responses organized by forms with analytics
3. **Response Analytics** - Get detailed statistics and insights

## Endpoints

### 1. Enhanced Submissions API

#### List All Submissions
```
GET /api/submissions/
```

**Features:**
- Returns detailed submission data with form information and responses
- Built-in search and filtering
- Pagination support

**Query Parameters:**
- `form`: Filter by form ID
- `status`: Filter by submission status (draft, submitted, under_review, approved, rejected)
- `submitted_by`: Filter by submitter (partial match)
- `search`: Search in submitted_by and form name
- `ordering`: Order by created_at, submitted_at, or status (use `-` for descending)

**Example:**
```
GET /api/submissions/?form=1&status=submitted&ordering=-created_at
```

#### Get Submissions by Form
```
GET /api/submissions/by_form/?form_id=1
```

**Query Parameters:**
- `form_id`: Required - Form ID to filter by
- `status`: Filter by submission status
- `date_from`: Filter submissions from this date (YYYY-MM-DD)
- `date_to`: Filter submissions until this date (YYYY-MM-DD)

#### Get Recent Submissions
```
GET /api/submissions/recent/?days=7
```

**Query Parameters:**
- `days`: Number of days back to look (default: 7)

#### Get Submission Statistics
```
GET /api/submissions/statistics/
```

Returns overall statistics including:
- Total submissions count
- Recent submissions (last 7 days)
- Breakdown by status
- Breakdown by form

### 2. Form Responses API

#### List Forms with Response Summary
```
GET /api/form-responses/
```

Returns all forms with basic statistics about their responses.

**Query Parameters:**
- `is_active`: Filter active/inactive forms (true/false)
- `search`: Search in form name and description
- `ordering`: Order by created_at (use `-` for descending)

#### Get Detailed Form with All Responses
```
GET /api/form-responses/{form_id}/
```

Returns comprehensive data for a specific form including:
- Form details
- All form fields
- All submissions with responses
- Response statistics

#### Get All Responses for a Form
```
GET /api/form-responses/{form_id}/responses/
```

**Query Parameters:**
- `status`: Filter by submission status
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `submitted_by`: Filter by submitter (partial match)

**Response includes:**
- Form basic information
- Total submissions count
- Detailed submission and response data

#### Get Form Analytics
```
GET /api/form-responses/{form_id}/analytics/
```

Returns detailed analytics including:
- Submission statistics by status
- Field-by-field response rates
- Option breakdown for dropdown fields
- Checkbox response distribution
- Average completion rate

### 3. Global Response Display

#### Get All Responses Across All Forms
```
GET /api/form-responses/all_responses/
```

**Query Parameters:**
- `form_id`: Filter by specific form
- `status`: Filter by submission status
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `page`: Page number (default: 1)
- `page_size`: Items per page (max: 100, default: 50)

**Features:**
- Paginated results
- Cross-form filtering
- Comprehensive response data

## Response Data Structure

### Detailed Submission Response
```json
{
  "id": 1,
  "form": {
    "id": 1,
    "name": "Customer Feedback Form",
    "description": "Please provide your feedback",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "submitted_by": "user@example.com",
  "status": "submitted",
  "submitted_at": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-15T14:30:00Z",
  "ip_address": "192.168.1.100",
  "response_count": 5,
  "responses": [
    {
      "id": 1,
      "field": {
        "id": 1,
        "label": "Full Name",
        "field_type": "text",
        "required": true,
        "options": null,
        "validation_type": "none",
        "order": 1
      },
      "formatted_value": "John Doe",
      "files": [],
      "value_text": "John Doe",
      "value_number": null,
      "value_date": null,
      "value_boolean": null,
      "value_json": null
    }
  ]
}
```

### Form Analytics Response
```json
{
  "form": {
    "id": 1,
    "name": "Customer Feedback Form",
    "total_fields": 5
  },
  "submission_analytics": {
    "total_submissions": 25,
    "recent_submissions": 8,
    "status_breakdown": [
      {"status": "submitted", "count": 20},
      {"status": "approved", "count": 5}
    ],
    "average_completion_rate": 95.5
  },
  "field_analytics": [
    {
      "field_id": 1,
      "field_label": "Full Name",
      "field_type": "text",
      "required": true,
      "total_responses": 25,
      "response_rate": 100.0
    },
    {
      "field_id": 2,
      "field_label": "Rating",
      "field_type": "dropdown",
      "required": false,
      "total_responses": 23,
      "response_rate": 92.0,
      "option_breakdown": {
        "Excellent": 10,
        "Good": 8,
        "Fair": 3,
        "Poor": 2
      }
    }
  ]
}
```

## Usage Examples

### View All Responses for a Specific Form
```bash
curl "http://localhost:8000/api/form-responses/1/responses/"
```

### Get Recent Submissions with Filtering
```bash
curl "http://localhost:8000/api/submissions/recent/?days=14"
```

### View Form Analytics
```bash
curl "http://localhost:8000/api/form-responses/1/analytics/"
```

### Get All Responses with Date Filter
```bash
curl "http://localhost:8000/api/form-responses/all_responses/?date_from=2024-01-01&date_to=2024-01-31&page_size=20"
```

### Filter Submissions by Status
```bash
curl "http://localhost:8000/api/submissions/?status=submitted&ordering=-created_at"
```

## Installation Requirements

To use the enhanced filtering features, install the following package:

```bash
pip install django-filter
```

Then add `'django_filters'` to your `INSTALLED_APPS` in settings.py.

## Features

- **Comprehensive Data**: Each response includes field details, formatted values, and file attachments
- **Flexible Filtering**: Filter by form, status, date range, and submitter
- **Analytics**: Detailed statistics including response rates and option breakdowns
- **Pagination**: Large datasets are automatically paginated
- **Search**: Full-text search across relevant fields
- **Real-time**: Data is always current as it reads directly from the database
- **Performance**: Optimized queries with select_related and prefetch_related

## Security Notes

- All endpoints require appropriate authentication (configure based on your needs)
- File uploads are handled securely with proper validation
- IP addresses are captured for audit trails
- Data is returned in a structured format suitable for admin interfaces

This API provides everything needed for a comprehensive admin interface to view and analyze all form responses in your dynamic forms system.