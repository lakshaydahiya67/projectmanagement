# Configuration Guide

This document provides a comprehensive guide to configuring the Project Management application through environment variables.

## Environment Variables Overview

The application uses environment variables for configuration. There are two main sets of environment variables:

1. **Backend (Django) Environment Variables** - Stored in `.env` file
2. **Frontend (React) Environment Variables** - Stored in `frontend/.env` file

## Setting Up Environment Variables

To set up your environment:

1. Copy the provided example files:
   ```bash
   # For backend
   cp env-example .env
   
   # For frontend
   cp frontend/.env-example frontend/.env
   ```
2. Edit the generated files with your specific values
3. Alternatively, run the setup script: `./setup_env.sh`

## Backend (Django) Environment Variables

### Core Django Settings

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `DJANGO_DEBUG` | Enable/disable debug mode | `True` | `False` |
| `DJANGO_SECRET_KEY` | Secret key for security | auto-generated | `your-secure-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | `example.com,api.example.com` |
| `DATABASE_PATH` | Path to SQLite database file | `db.sqlite3` | `/data/db.sqlite3` |
| `DEFAULT_PAGE_SIZE` | Default pagination size for API | `10` | `20` |

### Frontend Integration

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `FRONTEND_URL` | URL of the frontend application | `http://localhost:3000` | `https://app.example.com` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of origins allowed for CORS | `http://localhost:3000,http://127.0.0.1:3000` | `https://app.example.com` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF | `http://localhost:3000,http://127.0.0.1:3000` | `https://app.example.com` |
| `CORS_ALLOW_ALL_ORIGINS` | Allow all origins for CORS | `True` | `False` |

### Email Configuration

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.console.EmailBackend` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` | `smtp.sendgrid.net` |
| `EMAIL_PORT` | SMTP server port | `587` | `465` |
| `EMAIL_USE_TLS` | Use TLS for SMTP | `True` | `False` |
| `EMAIL_USE_SSL` | Use SSL for SMTP | `False` | `True` |
| `EMAIL_HOST_USER` | SMTP username | `` | `your-email@example.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password or app password | `` | `your-password` |
| `DEFAULT_FROM_EMAIL` | Default sender email address | `` | `noreply@example.com` |

### JWT Authentication

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `JWT_SIGNING_KEY` | Key used to sign JWT tokens | auto-generated | `your-secure-signing-key` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Lifetime of access tokens in minutes | `60` | `30` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Lifetime of refresh tokens in days | `7` | `14` |

### Redis & Celery

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `REDIS_HOST` | Redis hostname | `127.0.0.1` | `redis` |
| `REDIS_PORT` | Redis port | `6379` | `6380` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://localhost:6379/0` | `redis://redis:6379/0` |

## Frontend (React) Environment Variables

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `REACT_APP_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` | `https://api.example.com/api/v1` |
| `REACT_APP_WEBSOCKET_URL` | WebSocket server URL | `ws://localhost:8000/ws` | `wss://api.example.com/ws` |
| `REACT_APP_TOKEN_EXPIRY_THRESHOLD_MINS` | Minutes before token expiry to attempt refresh | `5` | `10` |
| `REACT_APP_ENABLE_ANALYTICS` | Enable analytics features | `true` | `false` |
| `REACT_APP_ENABLE_NOTIFICATIONS` | Enable notification features | `true` | `false` |
| `REACT_APP_DEFAULT_THEME` | Default UI theme | `light` | `dark` |
| `REACT_APP_ITEMS_PER_PAGE` | Default pagination size | `10` | `20` |
| `REACT_APP_FILE_UPLOAD_MAX_SIZE` | Maximum file upload size in bytes | `5242880` | `10485760` |

## Email Configuration Guide

### Gmail Setup

To use Gmail as your email provider:

1. Set the following variables in your `.env` file:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your.email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your.email@gmail.com
   ```

2. For `EMAIL_HOST_PASSWORD`, you need to create an App Password:
   - Go to your Google Account > Security
   - Enable 2-Step Verification if not already enabled
   - Under "App passwords", create a new app password for "Mail"
   - Use this generated password as your `EMAIL_HOST_PASSWORD`

### SendGrid Setup

To use SendGrid:

1. Sign up for a SendGrid account
2. Set up your variables:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=your-verified-sender@example.com
   ```

### Testing Email Configuration

Use the included email test script to verify your email configuration:

```bash
python -m email_test recipient@example.com
```

## Security Considerations

### Production Security Checklist

1. Generate strong, unique values for `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`:
   ```bash
   python generate_secure_keys.py
   ```

2. Set `DJANGO_DEBUG=False` in production

3. Configure appropriate values for `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`

4. Use HTTPS with SSL/TLS certificates

5. Set up proper email configuration with real credentials

6. Consider using a more robust database like PostgreSQL

7. Make sure Redis is secured behind a firewall or uses authentication

8. Implement rate limiting for API endpoints

### Best Practices

1. **Never hardcode environment variables in your code**. Always use the `.env` file or environment variables.
2. **Ensure your `.env` files are in `.gitignore`** to prevent committing sensitive information.
3. **Regularly rotate secrets** like JWT signing keys, especially after developer offboarding.
4. Consider using a secret management service for production environments.
5. Set appropriate file permissions for `.env` files to restrict access. 