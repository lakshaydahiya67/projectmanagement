# Environment Variables Documentation

This document describes all environment variables used in the Project Management application.

## Setting Up Environment Variables

The application uses environment variables for configuration. To set up your environment:

1. Copy the provided `env-example` file to `.env`: `cp env-example .env`
2. Edit the generated `.env` file with your specific values
3. Alternatively, run the setup script: `./setup_env.sh`

## Backend (Django) Environment Variables

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `DJANGO_DEBUG` | Debug mode flag | `True` | `False` |
| `DJANGO_SECRET_KEY` | Secret key for security | auto-generated | `your-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | `example.com,api.example.com` |
| `FRONTEND_URL` | URL of the frontend application | `http://localhost:3000` | `https://app.example.com` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of origins allowed to make cross-origin requests | `http://localhost:3000,http://127.0.0.1:3000` | `https://app.example.com` |
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
| `JWT_SIGNING_KEY` | Key used to sign JWT tokens | auto-generated | `your-signing-key` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Lifetime of access tokens in minutes | `60` | `30` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Lifetime of refresh tokens in days | `7` | `14` |

### Redis & Celery

| Variable | Description | Default Value | Example |
|----------|-------------|---------------|---------|
| `REDIS_HOST` | Redis hostname | `127.0.0.1` | `redis.example.com` |
| `REDIS_PORT` | Redis port | `6379` | `6380` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` | `redis://redis.example.com:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://localhost:6379/0` | `redis://redis.example.com:6379/0` |

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

## Email Configuration Guide

### Gmail

To use Gmail as your email provider:

1. Set the following variables in your `.env` file (copied from `env-example`):
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

### SendGrid

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

## Deployment Considerations

When deploying to production, make sure to:

1. Set `DJANGO_DEBUG=False`
2. Use strong, unique values for `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`
3. Update `ALLOWED_HOSTS` to include your domain
4. Configure proper email settings with real credentials
5. Set appropriate CORS settings for your domains

## Security Best Practices

1. **Never hardcode environment variables in your code**. Always use the `.env` file or environment variables.
2. **Ensure your `.env` files are in `.gitignore`** to prevent committing sensitive information.
3. **Regularly rotate secrets** like JWT signing keys, especially after developer offboarding.
4. Never commit your `.env` files to version control. The `env-example` files should be committed instead as templates.
5. Consider using a secret management service for production environments.