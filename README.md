# Project Management Application

A Trello/Asana-like project management application with real-time collaboration, task management, and analytics capabilities.

## 📑 Documentation

This project's documentation is organized into the following sections:

- **[Installation Guide](docs/INSTALLATION.md)** - Setup instructions for development and production
- **[Docker Guide](docs/DOCKER.md)** - Running the application with Docker
- **[Configuration Guide](docs/CONFIGURATION.md)** - Environment variables and configuration options
- **[API Documentation](docs/API.md)** - API endpoint reference and examples
- **[Development Guide](docs/DEVELOPMENT.md)** - Development workflow and best practices
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System architecture and component interactions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to this project

## 🚀 Features

- **Multi-tenant Architecture**: Organizations, projects, and user management
- **Task Management**: Kanban-style boards with cards and columns
- **Real-time Updates**: WebSocket integration for live collaboration
- **Analytics Dashboard**: Track project progress and team productivity
- **Activity Logs & Audit Trail**: Comprehensive logging of all user actions
- **Notifications System**: Email and in-app notifications
- **Role-based Access Control**: Admin, Manager, and Member roles
- **Responsive UI**: Works on desktop and mobile with dark mode support

## 🛠️ Tech Stack

### Backend
- Django 5.0.8
- Django Templates for UI
- Django REST Framework 3.15.2
- Django Channels for WebSockets (using in-memory channel layer)
- JWT Authentication

## 🚀 Deployment on Render.com

### Prerequisites
- A Render.com account
- GitHub repository with your code
- SQLite3 database (configured in the project)
- Redis instance (provided by Render)

### Setup Instructions

1. **Fork and Clone** the repository
2. **Set up Environment Variables**:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration
   - Make sure to set `RENDER=true` in your production environment

3. **Deploy to Render**:
   - Connect your GitHub repository to Render
   - Create a new Web Service
   - Create a Redis instance

4. **Environment Variables for Application**:
   ```
   DATABASE_PATH=/opt/render/project/src/db.sqlite3
   # Celery and Redis are no longer used
   DJANGO_SETTINGS_MODULE=projectmanagement.settings
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=False
   ```

5. **Build Commands**:
   - `chmod +x ./render-build.sh && ./render-build.sh`

6. **Start Commands**:
   - `gunicorn projectmanagement.wsgi:application --log-file -`

## 🏗️ Project Architecture

```
┌────────────────┐     
│                │     
│  Django        │
│  Application   │     
│                │     
└────────────────┘     
        ▲                      
        │                      
        └── WebSockets with in-memory channel layer
                              
```
```

For a detailed architecture overview, see the [Architecture Documentation](docs/ARCHITECTURE.md).

## 📋 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd projectmanagement

# Set up environment variables
cp env-example .env

# Run with Docker
docker-compose up -d

# Or for development setup
./setup_env.sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For detailed setup instructions, see the [Installation Guide](docs/INSTALLATION.md).

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project was created as part of a web application development course
- Inspired by productivity tools like Trello, Asana, and Jira 