# Docker Setup for Project Management Application

This guide provides instructions for setting up and running the Project Management application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

## Quick Start

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd projectmanagement
   ```

2. Set up environment variables:
   ```bash
   cp env-example .env
   cp frontend/.env-example frontend/.env
   ```
   
   Edit the `.env` file to update settings like secret keys, email configuration, etc.

3. Start the Docker containers:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost
   - API: http://localhost:8000/api/v1/
   - API Documentation: http://localhost:8000/api/docs/

## Docker Architecture

The application is composed of the following services:

- **frontend**: React frontend served via Nginx
- **backend**: Django REST API
- **redis**: Redis for WebSockets and Celery
- **celery_worker**: Celery worker for background tasks
- **celery_beat**: Celery scheduler for periodic tasks

## Data Persistence

The application uses the following Docker volumes:

- **sqlite_data**: Stores the SQLite database file
- **redis_data**: Stores Redis data

## Useful Commands

### View Logs

```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery_worker
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart a specific service
docker-compose restart backend
```

### Execute Commands Inside Containers

```bash
# Run Django management commands
docker-compose exec backend python manage.py check
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Test email configuration
docker-compose exec backend python -m email_test admin@example.com
```

### Scaling

You can scale the Celery workers if needed:

```bash
docker-compose up -d --scale celery_worker=3
```

## Production Considerations

For production deployment:

1. Set `DJANGO_DEBUG=False` in your .env file
2. Generate secure, unique values for `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`
3. Configure proper HTTPS with SSL/TLS (either via reverse proxy or by updating the Nginx configuration)
4. Set appropriate `ALLOWED_HOSTS` and CORS settings
5. Configure proper email settings with real credentials
6. Consider implementing a more robust database like PostgreSQL for larger deployments

## Troubleshooting

### Email Issues
If email sending fails, use the email test script:
```bash
docker-compose exec backend python -m email_test your-email@example.com
```

### WebSocket Connection Issues
Make sure the WebSocket URL in the frontend .env file is correct:
```
REACT_APP_WEBSOCKET_URL=ws://localhost/ws
```

### Database Access Issues
If there are issues with the SQLite database permissions, you may need to check the volume mounts:
```bash
docker-compose down
docker volume rm projectmanagement_sqlite_data
docker-compose up -d
``` 