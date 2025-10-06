# Dynamic Form Management System 

A comprehensive Django-based form builder and response management system similar to Google Forms, featuring real-time notifications, analytics, and a flexible API architecture.

##  Features

- **Dynamic Form Creation**: Build forms with multiple field types (text, number, date, dropdown, checkbox, file upload)
- **Real-Time Notifications**: WebSocket-powered live updates for new submissions
- **Flexible Response Collection**: Multiple API endpoints for different use cases
- **Advanced Analytics**: Response rates, completion statistics, and field-level insights  
- **File Upload Support**: Secure file handling with cloud storage integration
- **Smart Field Matching**: Tolerant field label matching for easy integration
- **Status Workflow**: Draft → Submitted → Under Review → Approved/Rejected
- **RESTful API**: Comprehensive API with multiple ViewSets for different workflows

##  Technology Stack

- **Backend**: Django 4.2.25 + Django REST Framework
- **Real-time**: Django Channels with WebSockets
- **Database**: SQLite (development) / PostgreSQL (production)
- **Task Queue**: Celery with Redis
- **File Storage**: Local (development) / AWS S3 (production)
- **Authentication**: JWT Token-based authentication

##  Prerequisites

- Python 3.8+ 
- Node.js 16+ (for frontend development)
- Redis Server (for real-time features and Celery)
- PostgreSQL (for production)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd myprojo
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (Development - SQLite)
DATABASE_URL=sqlite:///db.sqlite3

# Database Configuration (Production - PostgreSQL)
# DATABASE_URL=postgresql://username:password@localhost:5432/dbname

# Redis Configuration (for Channels and Celery)
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 Configuration (Production)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key  
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=us-west-2

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=True
```

### 5. Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
```

### 6. Install Redis (Required for Real-time Features)

**Windows:**
```powershell
# Using Chocolatey
choco install redis-64

# Or download from: https://github.com/microsoftarchive/redis/releases
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 7. Start Development Servers

**Terminal 1 - Django Development Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker (Optional):**
```bash
celery -A myprojo worker --loglevel=info
```

**Terminal 3 - Redis Server (if not running as service):**
```bash
redis-server
```

## 🚀 Quick Start

### 1. Access the Application

- **API Root**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **WebSocket**: ws://localhost:8000/ws/notifications/

### 2. Create Your First Form

**Using Django Admin:**
1. Go to http://localhost:8000/admin/
2. Login with your superuser account
3. Add a new Form in the "Forms" section
4. Add Fields to your form in the "Fields" section

**Using API:**
```bash
# Create a form
curl -X POST http://localhost:8000/api/forms/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contact Form",
    "description": "Get in touch with us",
    "is_active": true,
    "allow_multiple_submissions": false
  }'

# Add fields to the form
curl -X POST http://localhost:8000/api/fields/ \
  -H "Content-Type: application/json" \
  -d '{
    "form": 1,
    "label": "Full Name",
    "field_type": "text",
    "required": true,
    "order": 1
  }'
```

### 3. Submit Response to Form

```bash
curl -X POST http://localhost:8000/api/field-responses/ \
  -H "Content-Type: application/json" \
  -d '{
    "form_id": 1,
    "submitted_by": "user@example.com",
    "answers": {
      "Full Name": "John Doe",
      "Email": "john@example.com",
      "Message": "Hello, this is a test message!"
    }
  }'
```

## 📖 API Documentation

### Core Endpoints

| Endpoint | Description | Methods |
|----------|-------------|---------|
| `/api/forms/` | Form management | GET, POST, PUT, DELETE |
| `/api/fields/` | Field definitions | GET, POST, PUT, DELETE |
| `/api/submissions/` | Submission management | GET, POST, PUT, DELETE |
| `/api/field-responses/` | Client response API | GET, POST |
| `/api/form-responses/` | Form analytics & responses | GET |
| `/api/notifications/` | Real-time notifications | GET, POST |

### Advanced Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/submissions/recent/` | Recent submissions |
| `/api/submissions/statistics/` | Overall statistics |
| `/api/form-responses/{id}/analytics/` | Form-specific analytics |
| `/api/form-responses/{id}/responses/` | All responses for a form |
| `/api/form-responses/all_responses/` | Cross-form response view |

For detailed API documentation, see [FORM_RESPONSES_API.md](FORM_RESPONSES_API.md)

##  Project Structure

```
myprojo/
├── myprojo/                 # Django project settings
│   ├── settings.py         # Main settings
│   ├── urls.py             # URL routing  
│   ├── asgi.py            # ASGI configuration
│   └── wsgi.py            # WSGI configuration
├── forms_app/              # Form definitions
│   ├── models.py          # Form model
│   ├── views.py           # Form API views
│   ├── serializers.py     # Form serializers
│   └── admin.py           # Admin interface
├── fields_app/             # Dynamic field definitions
│   ├── models.py          # Field model with types & validation
│   ├── views.py           # Field API views  
│   └── serializers.py     # Field serializers
├── submissions_app/        # Response collection & analytics
│   ├── models.py          # Submission, FieldResponse, Notification
│   ├── views.py           # Multiple ViewSets for different use cases
│   ├── serializers.py     # Response serializers
│   ├── consumers.py       # WebSocket consumers
│   ├── routing.py         # WebSocket routing
│   └── tasks.py           # Celery tasks
├── templates/              # Django templates (if needed)
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── db.sqlite3             # SQLite database (development)
├── README.md              # This file
├── DESIGN_DECISIONS.md    # Architecture documentation
└── FORM_RESPONSES_API.md  # API documentation
```

## 🔧 Configuration

### Database Configuration

**Development (SQLite):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Production (PostgreSQL):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Redis Configuration

For real-time features and Celery:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
```

### File Storage Configuration

**Development (Local Storage):**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**Production (AWS S3):**
```python
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
```

## Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test forms_app
python manage.py test fields_app
python manage.py test submissions_app

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### API Testing

Use the provided test file:
```bash
python test_api_endpoints.py
```

Or test manually with curl:
```bash
# Test form creation
curl -X POST http://localhost:8000/api/forms/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Form", "description": "Test form description"}'
```

##  Deployment

### Production Checklist

1. **Environment Variables**: Set production values in `.env`
2. **Database**: Configure PostgreSQL connection
3. **Redis**: Set up Redis server for production  
4. **Static Files**: Configure static file serving
5. **File Storage**: Set up AWS S3 or similar
6. **Security**: Update `ALLOWED_HOSTS`, disable `DEBUG`
7. **SSL**: Configure HTTPS certificates
8. **Monitoring**: Set up application monitoring

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "myprojo.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/formdb
      - REDIS_URL=redis://redis:6379/0

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: formdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Support

- **Documentation**: See [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) for architecture details
- **API Docs**: See [FORM_RESPONSES_API.md](FORM_RESPONSES_API.md) for API reference
- **Issues**: Create an issue on GitHub for bugs or feature requests

