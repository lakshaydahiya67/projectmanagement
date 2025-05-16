# Docker Guide

This guide provides comprehensive instructions for setting up and running the Project Management application using Docker.

## Prerequisites

- Docker Engine 19.03.0+ 
- Docker Compose 1.27.0+
- Git (to clone the repository)

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repository-url>
   cd projectmanagement
   ```

2. **Set up environment variables:**
   ```bash
   cp env-example .env
   cp frontend/.env-example frontend/.env
   ```
   
   Edit the `.env` file to update settings like secret keys, email configuration, etc.

3. **Start the Docker containers:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost
   - API: http://localhost/api/v1/
   - API Documentation: http://localhost/api/docs/

## Docker Architecture

The application consists of the following services:

| Service | Description | Port |
|---------|-------------|------|
| **frontend** | React frontend served via Nginx | 80 (exposed) |
| **backend** | Django REST API | 8000 (internal) |
| **redis** | For WebSockets, caching, and Celery | 6379 (internal) |
| **celery_worker** | Celery worker for background tasks | - |
| **celery_beat** | Celery scheduler for periodic tasks | - |

## Configuration

The Docker setup can be configured through:

1. **Environment Variables** in `.env` file
2. **Docker Compose Overrides** - Create a `docker-compose.override.yml` file for environment-specific settings

### Important Configuration Options

- `DJANGO_DEBUG` - Set to `False` for production
- `DJANGO_SECRET_KEY` - Unique key for security
- `JWT_SIGNING_KEY` - Signing key for JWT tokens
- `ALLOWED_HOSTS` - List of allowed hostnames
- `FRONTEND_URL` - URL of the frontend application

## Data Persistence

The application uses the following Docker volumes:

- **sqlite_data**: Stores the SQLite database file
- **redis_data**: Stores Redis data for persistence
- **static_data**: Stores Django static files
- **media_data**: Stores user-uploaded media files

These volumes persist data even when containers are stopped or removed.

## Useful Commands

### View Logs

```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery_worker

# Follow logs in real-time
docker-compose logs -f backend
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
docker-compose exec backend python manage.py createsuperuser

# Test email configuration
docker-compose exec backend python -m email_test admin@example.com

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Scaling

You can scale the Celery workers if needed:

```bash
docker-compose up -d --scale celery_worker=3
```

## Production Considerations

For production deployment:

1. **Security Settings**
   - Set `DJANGO_DEBUG=False` in your .env file
   - Generate secure, unique values for `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`
   - Configure proper HTTPS with SSL/TLS
   - Set appropriate `ALLOWED_HOSTS` and CORS settings
   - Configure proper email settings with real credentials
   - Secure Redis with a password

2. **Performance Optimization**
   - Consider implementing a more robust database like PostgreSQL
   - Configure appropriate resource limits for containers
   - Set up proper logging levels

3. **Deployment Options**
   - Deploy with Docker Swarm or Kubernetes for high availability
   - Use Docker registry for image distribution
   - Implement CI/CD pipeline for automated deployments

## Troubleshooting

### Common Issues

#### Container Fails to Start

```bash
# Check container logs
docker-compose logs <service_name>

# Check container status
docker-compose ps
```

#### Email Issues

If email sending fails, use the email test script:
```bash
docker-compose exec backend python -m email_test your-email@example.com
```

Common email issues:
- Incorrect SMTP credentials
- Gmail requires App Password if using 2FA
- Firewall blocking outgoing SMTP connections

#### WebSocket Connection Issues

Make sure the WebSocket URL in the frontend .env file is correct:
```
REACT_APP_WEBSOCKET_URL=ws://localhost/ws
```

If WebSockets aren't working:
- Check if Redis is running
- Verify Nginx is properly configured for WebSocket proxying
- Check browser console for connection errors

#### Database Access Issues

If there are issues with the SQLite database permissions, you may need to check the volume mounts:
```bash
docker-compose down
docker volume rm projectmanagement_sqlite_data
docker-compose up -d
```

#### Static Files Not Loading

If static files aren't loading properly:
```bash
docker-compose exec backend python manage.py collectstatic --noinput
docker-compose restart frontend
```

### Advanced Troubleshooting

#### Inspect Container Details

```bash
docker inspect <container_id>
```

#### Check Network Connectivity

```bash
docker-compose exec backend ping redis
```

#### View Resource Usage

```bash
docker stats
```

## Upgrading

To upgrade the application:

1. Pull the latest changes from the repository
   ```bash
   git pull
   ```

2. Rebuild and restart the containers
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. Run migrations if needed
   ```bash
   docker-compose exec backend python manage.py migrate
   ``` 