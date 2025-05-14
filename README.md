# Project Management Application

A Trello/Asana-like project management application with real-time collaboration, task management, and analytics capabilities.

## Features

- **Multi-tenant Architecture**: Organizations, projects, and user management
- **Task Management**: Kanban-style boards with cards and columns
- **Real-time Updates**: WebSocket integration for live collaboration
- **Analytics Dashboard**: Track project progress and team productivity
- **Activity Logs & Audit Trail**: Comprehensive logging of all user actions
- **Notifications System**: Email and in-app notifications
- **Role-based Access Control**: Admin, Manager, and Member roles
- **Responsive UI**: Works on desktop and mobile with dark mode support

## Tech Stack

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

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis server (for WebSockets and Celery)

### Environment Setup

1. Create a `.env` file in the project root using the provided template:
```
cp env.example .env
```

2. Customize the environment variables as needed

### Backend Setup

1. Clone the repository
```
git clone <repository-url>
cd projectmanagement
```

2. Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Run migrations
```
python manage.py migrate
```

5. Create a superuser
```
python manage.py createsuperuser
```

6. Start the development server
```
python manage.py runserver
```

7. In a separate terminal, start Celery worker
```
celery -A projectmanagement worker --loglevel=info
```

8. For WebSocket support, ensure Redis is running
```
redis-server
```

### Frontend Setup

1. Navigate to the frontend directory
```
cd frontend
```

2. Install dependencies
```
npm install
```

3. Start the development server
```
npm start
```

## Using the Application

### Activity Logs & Audit Trail
- Access the activity logs by clicking on "Activity Logs" in the main navigation
- Filter logs by date, user, action type, or content type
- Project-specific activity can be viewed from the project's activity tab

### User Registration
- Register using email, username, and password
- The system will create a default user preference profile automatically

### Creating Projects & Tasks
1. Create an organization first
2. Create projects within the organization
3. Create boards within projects
4. Add columns to boards
5. Create and assign tasks within columns

### Real-time Collaboration
- Multiple users can view and edit the same board simultaneously
- Changes are reflected in real-time via WebSockets

## API Documentation

API documentation is available at:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project was created as part of a web application development course
- Inspired by productivity tools like Trello, Asana, and Jira 