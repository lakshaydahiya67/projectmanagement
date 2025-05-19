# Environment Variable Documentation

This document provides a comprehensive overview of all environment variables used in the Project Management application, how they are configured, and how they affect different components of the system.

## Environment Configuration Overview

The application uses a centralized `.env` file in the project root directory to manage all environment variables. This file contains configurations for both Docker and local development environments, with local development variables commented out when using Docker.

## Core Environment Variables

### Django Configuration

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `DJANGO_DEBUG` | Enables Django debug mode | `True` or `False` |
| `DJANGO_SECRET_KEY` | Django secret key for security | `your-secret-key-here` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,backend` |

### URL Configuration

#### Docker Environment

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `FRONTEND_URL` | Base URL for the frontend | `http://localhost` |
| `BACKEND_URL` | Base URL for the backend API | `http://localhost/api/v1` |
| `WEBSOCKET_URL` | WebSocket URL for real-time features | `ws://localhost/ws` |

#### Local Development Environment

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `FRONTEND_URL` | Base URL for the frontend | `http://localhost:3000` |
| `BACKEND_URL` | Base URL for the backend API | `http://localhost:8000/api/v1` |
| `WEBSOCKET_URL` | WebSocket URL for real-time features | `ws://localhost:8000/ws` |

### Redis and Celery Configuration

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `REDIS_HOST` | Redis host address | `redis` (Docker) or `localhost` (local) |
| `REDIS_PORT` | Redis port | `6379` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://redis:6379/0` or `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://redis:6379/0` or `redis://localhost:6379/0` |

### CORS and CSRF Settings

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins for CORS | `http://localhost,http://127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF | `http://localhost,http://127.0.0.1` |
| `CORS_ALLOW_ALL_ORIGINS` | Allow CORS for all origins | `True` or `False` |

### Email Configuration

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `EMAIL_BACKEND` | Django email backend | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS for email | `True` or `False` |
| `EMAIL_HOST_USER` | SMTP username | `example@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `your-password` |
| `DEFAULT_FROM_EMAIL` | Default sender email address | `example@gmail.com` |

### JWT Settings

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `JWT_SIGNING_KEY` | Secret key for JWT signing | `your-jwt-signing-key` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime in minutes | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token lifetime in days | `7` |

### Frontend React Configuration

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `REACT_APP_API_URL` | API URL for frontend (passed from `BACKEND_URL`) | `http://localhost/api/v1` |
| `REACT_APP_WEBSOCKET_URL` | WebSocket URL for frontend (passed from `WEBSOCKET_URL`) | `ws://localhost/ws` |
| `REACT_APP_TOKEN_EXPIRY_THRESHOLD_MINS` | Token expiry threshold in minutes | `5` |
| `REACT_APP_ENABLE_ANALYTICS` | Enable analytics features | `true` or `false` |
| `REACT_APP_ENABLE_NOTIFICATIONS` | Enable notification features | `true` or `false` |
| `REACT_APP_DEFAULT_THEME` | Default application theme | `light` or `dark` |
| `REACT_APP_ITEMS_PER_PAGE` | Number of items to display per page | `10` |
| `REACT_APP_FILE_UPLOAD_MAX_SIZE` | Maximum file upload size in bytes | `5242880` (5MB) |

## Environment Variable Flow

1. **Docker Environment**:
   - Variables from `.env` file are loaded into the Docker environment
   - Docker Compose passes these variables to the containers
   - For the frontend, build-time ARGs are provided to create environment-specific builds

2. **Local Development**:
   - Uncomment the local development section in the `.env` file
   - Comment out the Docker environment section
   - Run the backend and frontend directly using their respective development servers

## Switching Between Environments

1. **Docker to Local**:
   - Comment out the Docker environment variables section
   - Uncomment the local development variables section
   - Run the backend and frontend separately with their development servers

2. **Local to Docker**:
   - Comment out the local development section
   - Uncomment the Docker environment section
   - Run `docker compose up -d` to start the containers

## Important Notes

- **Static Files**: Static files are served from a shared volume between the backend and frontend containers in Docker
- **Email Settings**: For local development, you can use the console email backend for testing
- **Security**: Ensure that sensitive information like secret keys and passwords are not committed to version control
