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
- Django 4.2.11
- Django REST Framework 3.14.0
- Django Channels for WebSockets
- Celery + Redis for background tasks
- JWT Authentication

### Frontend
- React 18.2.0
- React Router 6
- Tailwind CSS
- Chart.js for data visualization
- React Beautiful DND for drag-and-drop

## 🏗️ Project Architecture

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│  React         │     │  Django        │     │  Celery        │
│  Frontend      │◄────┤  Backend       │◄────┤  Workers       │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
        ▲                      ▲                      ▲
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                              │
                     ┌────────────────┐
                     │                │
                     │  Redis         │
                     │  (WS/Cache)    │
                     │                │
                     └────────────────┘
```

For a detailed architecture overview, see the [Architecture Documentation](docs/ARCHITECTURE.md).

## 📋 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd projectmanagement

# Set up environment variables
cp env-example .env
cp frontend/.env-example frontend/.env

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