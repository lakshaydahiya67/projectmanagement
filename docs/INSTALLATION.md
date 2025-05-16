# Installation Guide

This guide provides detailed instructions for setting up the Project Management application in various environments.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Redis server (for WebSockets and Celery)
- Git

## Development Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd projectmanagement
   ```

2. **Set up environment variables**
   ```bash
   cp env-example .env
   # Edit the .env file with your specific values
   nano .env
   ```
   
   Alternatively, run the included setup script:
   ```bash
   ./setup_env.sh
   ```

3. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Set up environment variables**
   ```bash
   cp .env-example .env
   # Edit the .env file with your specific values
   nano .env
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

### Running Background Services

1. **Start Celery worker**
   ```bash
   # In a separate terminal
   source venv/bin/activate
   celery -A projectmanagement worker --loglevel=info
   ```

2. **Start Celery beat (for scheduled tasks)**
   ```bash
   # In a separate terminal
   source venv/bin/activate
   celery -A projectmanagement beat --loglevel=info
   ```

3. **Ensure Redis is running**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # If not running, start Redis
   redis-server
   ```

## Production Setup

For production deployment, follow these additional steps:

1. **Generate secure keys**
   ```bash
   python generate_secure_keys.py
   ```
   This script will generate secure keys for Django and JWT authentication.

2. **Update production settings**
   - Set `DJANGO_DEBUG=False` in your .env file
   - Configure proper `ALLOWED_HOSTS` and CORS settings
   - Set up proper email configuration
   - Use a production-ready database like PostgreSQL
   - Secure Redis behind a firewall or with authentication

3. **Set up a production web server**
   We recommend using Nginx with Gunicorn for Django:
   ```bash
   # Install Gunicorn
   pip install gunicorn
   
   # Run Django with Gunicorn
   gunicorn projectmanagement.wsgi:application --bind 0.0.0.0:8000
   ```

4. **Build the frontend for production**
   ```bash
   cd frontend
   npm run build
   ```
   Serve the built files from Nginx or another web server.

5. **Set up SSL/TLS for HTTPS**
   Configure Nginx with SSL certificates (Let's Encrypt is recommended).

## Docker Setup

For Docker-based deployment, refer to the [Docker Guide](DOCKER.md) for detailed instructions.

## Verification

After setting up the application, verify it's working correctly:

1. Access the Django admin interface at `http://localhost:8000/admin/`
2. Access the frontend at `http://localhost:3000/` (development) or your configured domain
3. Access the API documentation at `http://localhost:8000/api/docs/`
4. Test the API endpoints using the provided documentation

## Next Steps

- Configure [environment variables](CONFIGURATION.md) for your specific needs
- Review the [architecture overview](ARCHITECTURE.md) to understand the system
- Check out the [development guide](DEVELOPMENT.md) for best practices 