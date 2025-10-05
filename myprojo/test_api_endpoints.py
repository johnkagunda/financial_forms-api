#!/usr/bin/env python
"""
Test script to demonstrate the new form responses API endpoints.
This script shows all available endpoints and provides example usage.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"

def print_endpoint(name, method, url, description):
    print(f"\n{name}")
    print("="*50)
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"Description: {description}")
    print("-"*50)

def main():
    print("FORM RESPONSES API ENDPOINTS")
    print("="*80)
    print("This script demonstrates the new comprehensive API endpoints for viewing")
    print("all form responses from your dynamically created forms.")
    print("="*80)

    # Enhanced Submissions API
    print("\n1. ENHANCED SUBMISSIONS API")
    print("="*40)
    
    print_endpoint(
        "List All Submissions (Enhanced)",
        "GET",
        f"{BASE_URL}/submissions/",
        "Returns all submissions with detailed form and response data. Supports filtering and search."
    )
    
    print("Query Parameters:")
    print("- form: Filter by form ID")
    print("- status: Filter by submission status")
    print("- submitted_by: Filter by submitter")
    print("- search: Search in submitted_by and form name")
    print("- ordering: Order results")
    
    print_endpoint(
        "Get Submissions by Form",
        "GET",
        f"{BASE_URL}/submissions/by_form/?form_id=1",
        "Get all submissions for a specific form with optional filtering."
    )
    
    print_endpoint(
        "Get Recent Submissions",
        "GET",
        f"{BASE_URL}/submissions/recent/?days=7",
        "Get submissions from the last N days (default 7)."
    )
    
    print_endpoint(
        "Get Submission Statistics",
        "GET",
        f"{BASE_URL}/submissions/statistics/",
        "Get overall statistics about all submissions."
    )

    # Form Responses API
    print("\n\n2. FORM RESPONSES API")
    print("="*40)
    
    print_endpoint(
        "List Forms with Response Summary",
        "GET",
        f"{BASE_URL}/form-responses/",
        "Get all forms with basic response statistics."
    )
    
    print_endpoint(
        "Get Detailed Form with All Responses",
        "GET",
        f"{BASE_URL}/form-responses/1/",
        "Get comprehensive data for a specific form including all fields and responses."
    )
    
    print_endpoint(
        "Get All Responses for a Form",
        "GET",
        f"{BASE_URL}/form-responses/1/responses/",
        "Get detailed responses for a specific form with filtering options."
    )
    
    print("Query Parameters:")
    print("- status: Filter by submission status")
    print("- date_from: Filter from date (YYYY-MM-DD)")
    print("- date_to: Filter to date (YYYY-MM-DD)")
    print("- submitted_by: Filter by submitter")
    
    print_endpoint(
        "Get Form Analytics",
        "GET",
        f"{BASE_URL}/form-responses/1/analytics/",
        "Get detailed analytics including response rates and field breakdowns."
    )
    
    print_endpoint(
        "Get All Responses Across All Forms",
        "GET",
        f"{BASE_URL}/form-responses/all_responses/",
        "Get paginated responses across all forms with comprehensive filtering."
    )
    
    print("Query Parameters:")
    print("- form_id: Filter by specific form")
    print("- status: Filter by submission status")
    print("- date_from, date_to: Date range filter")
    print("- page: Page number")
    print("- page_size: Items per page")

    # Usage Examples
    print("\n\n3. USAGE EXAMPLES")
    print("="*40)
    
    examples = [
        ("View all submissions", f"{BASE_URL}/submissions/"),
        ("Filter submissions by form", f"{BASE_URL}/submissions/?form=1&status=submitted"),
        ("Get recent submissions", f"{BASE_URL}/submissions/recent/?days=14"),
        ("View form analytics", f"{BASE_URL}/form-responses/1/analytics/"),
        ("Get filtered responses", f"{BASE_URL}/form-responses/1/responses/?status=submitted&date_from=2024-01-01"),
        ("Paginated all responses", f"{BASE_URL}/form-responses/all_responses/?page=1&page_size=20"),
    ]
    
    for desc, url in examples:
        print(f"\n{desc}:")
        print(f"curl \"{url}\"")

    # Data Structure Examples
    print("\n\n4. RESPONSE DATA STRUCTURE")
    print("="*40)
    
    example_response = {
        "id": 1,
        "form": {
            "id": 1,
            "name": "Customer Feedback Form",
            "description": "Please provide feedback",
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z"
        },
        "submitted_by": "user@example.com",
        "status": "submitted",
        "submitted_at": "2024-01-15T14:30:00Z",
        "response_count": 3,
        "responses": [
            {
                "id": 1,
                "field": {
                    "id": 1,
                    "label": "Full Name",
                    "field_type": "text",
                    "required": True
                },
                "formatted_value": "John Doe",
                "value_text": "John Doe"
            }
        ]
    }
    
    print("Example Submission Response:")
    print(json.dumps(example_response, indent=2))

    print("\n\n5. FEATURES")
    print("="*40)
    features = [
        "✓ Comprehensive response data with field details",
        "✓ Flexible filtering by form, status, date, submitter",
        "✓ Advanced analytics with response rates and breakdowns",
        "✓ Pagination for large datasets",
        "✓ Search functionality",
        "✓ Real-time data",
        "✓ Optimized database queries",
        "✓ Support for all field types (text, number, date, dropdown, checkbox, file)",
        "✓ File attachment handling",
        "✓ Status tracking and workflows"
    ]
    
    for feature in features:
        print(feature)

    print("\n\n6. QUICK START")
    print("="*40)
    print("1. Ensure your Django server is running:")
    print("   python manage.py runserver")
    print()
    print("2. Test basic functionality:")
    print(f"   curl {BASE_URL}/form-responses/")
    print()
    print("3. View comprehensive form data:")
    print(f"   curl {BASE_URL}/form-responses/1/")
    print()
    print("4. Get detailed analytics:")
    print(f"   curl {BASE_URL}/form-responses/1/analytics/")
    
    print("\n" + "="*80)
    print("For complete documentation, see FORM_RESPONSES_API.md")
    print("="*80)

if __name__ == "__main__":
    main()