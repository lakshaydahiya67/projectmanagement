# Project Management Application

A clean, simple project management application built with Django and Django REST Framework. Features task management, team collaboration, and project organization.

## 🚀 Features

- **Multi-tenant Architecture**: Organizations, projects, and user management
- **Task Management**: Kanban-style boards with tasks and columns
- **Team Collaboration**: User roles and project membership
- **Activity Tracking**: Comprehensive logging of all user actions
- **Email Notifications**: User registration and password reset emails
- **RESTful API**: Full API with Swagger/OpenAPI documentation
- **Session Authentication**: Simple, secure Django session-based auth

## 🛠️ Tech Stack

### Backend
- **Django 5.0.8** - Web framework
- **Django REST Framework 3.16.1** - RESTful API
- **SQLite** - Database (simple and reliable)
- **Session Authentication** - Built-in Django auth
- **SendGrid** - Email delivery
- **WhiteNoise** - Static file serving

### API & Documentation
- **drf-yasg** - Swagger/OpenAPI documentation
- **django-filter** - API filtering
- **django-cors-headers** - CORS handling

## 📋 Quick Start

### Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd projectmanagement
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
python manage.py migrate
python manage.py createsuperuser
```

3. **Run the server**:
```bash
python manage.py runserver
```

4. **Access the application**:
- **Main app**: http://localhost:8000/
- **Admin panel**: http://localhost:8000/admin/
- **API docs**: http://localhost:8000/api/docs/
- **API (ReDoc)**: http://localhost:8000/api/redoc/

## 🔗 API Endpoints

The REST API provides full CRUD operations for:

- `/api/v1/users/` - User management
- `/api/v1/organizations/` - Organization management
- `/api/v1/projects/` - Project management
- `/api/v1/tasks/` - Task management with labels, comments, attachments
- `/api/v1/notifications/` - User notifications
- `/api/v1/analytics/` - Analytics and reporting
- `/api/v1/activity-logs/` - Activity logs and audit trail

Full API documentation available at `/api/docs/` when running the server.

## 🗂️ Project Structure

```
projectmanagement/
├── projectmanagement/          # Main Django project
├── users/                      # User management & auth
├── organizations/              # Organization management
├── projects/                   # Project management
├── tasks/                      # Task management
├── notifications/              # User notifications
├── analytics/                  # Analytics & reporting
├── activitylogs/              # Activity logging
├── templates/                  # HTML templates
├── static/                     # Static files
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management
└── README.md                  # This file
```

## 🚀 Deployment

### Render.com Deployment

1. **Prepare your repository**:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. **Create a Web Service on Render**:
- Connect your GitHub repository
- **Runtime**: Python 3
- **Build Command**: `chmod +x ./build.sh && ./build.sh build`
- **Start Command**: `gunicorn projectmanagement.wsgi:application --bind 0.0.0.0:$PORT`

3. **Environment Variables** (set in Render dashboard):
```
DJANGO_SETTINGS_MODULE=projectmanagement.settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.onrender.com,localhost
DATABASE_PATH=/opt/render/project/src/db.sqlite3

# Email (SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

4. **Deploy**: Click "Create Web Service" and wait for deployment.

## 🔧 Configuration

### Email Setup (Optional)

For email notifications, configure SendGrid:

1. Create a SendGrid account
2. Get your API key
3. Set environment variables (see deployment section)

For development, emails will print to console by default.

### Database

- **Development**: SQLite (included)
- **Production**: SQLite (works well for small-medium apps)
- **Scaling**: Consider PostgreSQL for larger datasets

## 🛡️ Security Features

- Session-based authentication (secure by default)
- CSRF protection enabled
- CORS headers configured
- Activity logging for audit trails
- Secure password validation
- Production security settings for HTTPS

## 📊 What's Included

### User Management
- User registration and authentication
- User profiles and preferences
- Password reset functionality
- Activity logging

### Project Management
- Organizations and team management
- Projects with member roles
- Kanban-style task boards
- Task labels, comments, and attachments

### API Features
- Full REST API for all resources
- Swagger/OpenAPI documentation
- Filtering and pagination
- Permission-based access control

## 🔄 Architecture

This is a simplified, maintainable Django application:

```
┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   API Clients   │
│                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────────────┐
          │   Django Application    │
          │                         │
          │  ┌─────────────────┐    │
          │  │ Session Auth    │    │
          │  │ (No JWT/tokens) │    │
          │  └─────────────────┘    │
          │                         │
          │  ┌─────────────────┐    │
          │  │ Django REST     │    │
          │  │ Framework       │    │
          │  └─────────────────┘    │
          │                         │
          │  ┌─────────────────┐    │
          │  │ SQLite          │    │
          │  │ Database        │    │
          │  └─────────────────┘    │
          └─────────────────────────┘
```

**Key Design Decisions**:
- **Session Authentication**: Simple, secure, no token management
- **SQLite Database**: Simple setup, good performance for most use cases
- **No WebSockets**: Simplified architecture, traditional HTTP requests
- **No Background Tasks**: All processing is synchronous
- **Django Templates + API**: Flexible for both web and API clients

## 📈 Performance & Scaling

- **Current Setup**: Suitable for small to medium teams
- **Database**: SQLite handles thousands of tasks efficiently
- **Scaling Options**: Easy upgrade path to PostgreSQL
- **Caching**: Can add Redis caching if needed
- **CDN**: Static files can be served via CDN

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. See license details in the repository.

## 🆘 Support

- Check the logs for error details
- Ensure all environment variables are set correctly
- Verify database migrations are applied
- For deployment issues, check Render.com logs

---

**Simple. Reliable. Scalable.**

This project prioritizes maintainability and simplicity while providing all the essential features for project management.