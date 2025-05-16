# Development Guide

This guide provides information on development workflows, coding standards, and best practices for the Project Management application.

## Development Environment Setup

Follow the [Installation Guide](INSTALLATION.md) to set up your development environment.

## Development Workflow

### 1. Git Workflow

We follow a feature branch workflow:

1. **Create a feature branch**

   ```bash
   # Update main branch
   git checkout main
   git pull
   
   # Create a feature branch
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**

   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

3. **Push changes and create a pull request**

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Code review and merge**
   - Create a pull request on GitHub
   - Await code review
   - Address feedback
   - Merge pull request

### 2. Backend Development

#### Running the Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the development server
python manage.py runserver
```

#### Creating Django Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

#### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific tests
python manage.py test users.tests
```

### 3. Frontend Development

#### Running the Development Server

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm start
```

#### Building for Production

```bash
# Build frontend
npm run build
```

#### Running Tests

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Code Standards

### Python Code Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) coding style
- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use docstrings for all functions, classes, and modules
- Write unit tests for all new functionality

Example Python code:

```python
def calculate_task_completion(project_id):
    """
    Calculate the completion percentage of tasks in a project.
    
    Args:
        project_id (uuid): The UUID of the project
        
    Returns:
        float: The percentage of completed tasks (0-100)
    """
    tasks = Task.objects.filter(project_id=project_id)
    if not tasks.exists():
        return 0
    
    completed = tasks.filter(status='completed').count()
    total = tasks.count()
    
    return (completed / total) * 100
```

### JavaScript/React Code Standards

- Use ES6+ syntax
- Use camelCase for variables and functions
- Use PascalCase for component names
- Maximum line length of 100 characters
- Use JSDoc comments for functions
- Prefer functional components with hooks over class components

Example React component:

```jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { fetchTasks } from '../api/tasks';

/**
 * Component for displaying task items in a project
 */
const TaskList = ({ projectId }) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadTasks = async () => {
      try {
        setLoading(true);
        const data = await fetchTasks(projectId);
        setTasks(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadTasks();
  }, [projectId]);
  
  if (loading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <ul className="task-list">
      {tasks.map(task => (
        <li key={task.id} className="task-item">
          <h3>{task.title}</h3>
          <p>{task.description}</p>
          <span className={`status status-${task.status}`}>{task.status}</span>
        </li>
      ))}
    </ul>
  );
};

TaskList.propTypes = {
  projectId: PropTypes.string.isRequired
};

export default TaskList;
```

## API Development

### Adding a New Endpoint

1. Define the serializer in a `serializers.py` file
2. Create the view in a `views.py` file
3. Add the URL pattern in a `urls.py` file
4. Document the API in the API documentation
5. Write tests for the new endpoint

Example:

```python
# serializers.py
from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'assignee', 'due_date']

# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(project__organization__members=self.request.user)

# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
```

## WebSocket Development

### Adding a New WebSocket Consumer

1. Define the consumer in a `consumers.py` file
2. Add the WebSocket URL pattern in a `routing.py` file
3. Test the WebSocket connection

Example:

```python
# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class TaskConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        message_type = content.get('type')
        
        if message_type == 'task.update':
            # Handle task update
            task_data = content.get('data')
            # Process data (save to database, etc.)
            
            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'task_update',
                    'data': task_data
                }
            )
    
    async def task_update(self, event):
        # Send message to WebSocket
        await self.send_json(event)
```

## Debugging

### Backend Debugging

- Use Django Debug Toolbar for debugging database queries, templates, etc.
- Use `pdb` or `ipdb` for Python debugging:

```python
import pdb; pdb.set_trace()  # Add this line where you want to debug
```

### Frontend Debugging

- Use React Developer Tools browser extension
- Use browser console and debugging tools
- Use inline debugging with `console.log` or `debugger` statement:

```javascript
console.log('Variable value:', someVariable);
debugger;  // Will pause execution in browser devtools
```

## Performance Optimization

### Backend Optimization

- Use `select_related` and `prefetch_related` to reduce database queries
- Use caching for expensive operations
- Use Django Debug Toolbar to identify and fix N+1 query problems

Example:

```python
# Bad (causes N+1 queries)
tasks = Task.objects.filter(project_id=project_id)
for task in tasks:
    print(task.assignee.username)  # Each access causes a new query

# Good (performs a JOIN)
tasks = Task.objects.filter(project_id=project_id).select_related('assignee')
for task in tasks:
    print(task.assignee.username)  # Uses data from the JOIN
```

### Frontend Optimization

- Use React.memo for pure components
- Use useMemo and useCallback hooks for expensive calculations
- Implement virtualization for long lists
- Use code splitting for lazy loading

Example:

```jsx
// Bad
const TaskList = ({ tasks }) => {
  const sortedTasks = tasks.sort((a, b) => a.priority - b.priority);
  
  return (
    <ul>
      {sortedTasks.map(task => <TaskItem key={task.id} task={task} />)}
    </ul>
  );
};

// Good
const TaskList = ({ tasks }) => {
  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => a.priority - b.priority);
  }, [tasks]);
  
  return (
    <ul>
      {sortedTasks.map(task => <TaskItem key={task.id} task={task} />)}
    </ul>
  );
};
```

## Continuous Integration

We use GitHub Actions for CI/CD. To ensure your code passes CI:

1. Run tests locally before pushing
2. Make sure all linting issues are fixed
3. Ensure test coverage meets requirements
4. Write tests for new functionality

## Tips and Best Practices

1. **Security First**
   - Never hardcode secrets
   - Validate all user inputs
   - Apply principle of least privilege

2. **Code Organization**
   - Follow Django's app-based structure
   - Use React's feature-based folder structure
   - Keep components small and focused

3. **Testing**
   - Write tests as you develop
   - Aim for high test coverage
   - Test edge cases

4. **Documentation**
   - Document code with docstrings and comments
   - Update API documentation when changing endpoints
   - Document complex business logic

5. **Collaboration**
   - Communicate changes to the team
   - Ask for help when stuck
   - Provide constructive code reviews 