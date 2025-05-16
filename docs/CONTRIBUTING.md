# Contributing Guide

Thank you for your interest in contributing to the Project Management application! This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)
- [Security Vulnerability Reporting](#security-vulnerability-reporting)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

Please ensure you have the following installed:

- Python 3.8+
- Node.js 16+
- Redis
- Git

### Setup for Development

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/projectmanagement.git
   cd projectmanagement
   ```
3. Set up your development environment:
   ```bash
   # Set up Python environment
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Set up environment variables
   cp env-example .env
   # Edit .env with your values
   
   # Set up database
   python manage.py migrate
   
   # Create a superuser
   python manage.py createsuperuser
   
   # Set up frontend
   cd frontend
   cp .env-example .env
   npm install
   ```
4. Run the application:
   ```bash
   # In one terminal (backend)
   python manage.py runserver
   
   # In another terminal (frontend)
   cd frontend
   npm start
   ```

## Development Process

### Branching Strategy

We follow a feature branch workflow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/feature-name` - Feature branches
- `bugfix/issue-description` - Bug fix branches
- `hotfix/issue-description` - Hot fixes for production

### Development Workflow

1. Ensure you're working on the latest version of the code:
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes, following the coding standards

4. Add and commit your changes with a meaningful commit message:
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

5. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request against the `develop` branch

## Pull Request Guidelines

When creating a pull request, please:

1. Create a clear, concise PR title and description
2. Link to any related issues
3. Include screenshots or GIFs for UI changes
4. Ensure all tests pass
5. Ensure code linting passes
6. Make sure documentation is updated if needed
7. Describe any breaking changes

### PR Review Process

All PRs will be reviewed by at least one maintainer. The reviewer may:
- Approve the PR
- Request changes
- Provide general feedback

Once approved, a maintainer will merge the PR.

## Coding Standards

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use docstrings for functions, classes, and modules
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Add type hints where appropriate

```python
def calculate_completion_percentage(tasks: List[Task]) -> float:
    """
    Calculate the percentage of completed tasks.
    
    Args:
        tasks: A list of Task objects
        
    Returns:
        The percentage of completed tasks as a float between 0 and 100
    """
    if not tasks:
        return 0
    
    completed_count = sum(1 for task in tasks if task.status == 'completed')
    return (completed_count / len(tasks)) * 100
```

### JavaScript/React Code

- Use ESLint and Prettier for code formatting
- Use functional components with hooks
- Use meaningful component names
- Document complex logic with comments
- Follow React best practices

```jsx
/**
 * Component for displaying a list of tasks with filtering
 */
function TaskList({ projectId, filters }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch tasks when projectId or filters change
    const fetchTasks = async () => {
      setLoading(true);
      try {
        const response = await api.getTasks(projectId, filters);
        setTasks(response.data);
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTasks();
  }, [projectId, filters]);
  
  return (
    <div className="task-list">
      {loading ? (
        <Spinner />
      ) : (
        tasks.map(task => <TaskItem key={task.id} task={task} />)
      )}
    </div>
  );
}
```

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This means commits should be formatted as:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types include:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or correcting tests
- `chore`: Changes to the build process, tools, etc.

Example:
```
feat(tasks): add drag-and-drop functionality to task board

- Implement drag-and-drop using react-beautiful-dnd
- Update task position via API when dropped
- Add visual feedback during drag

Closes #123
```

## Testing Guidelines

### Backend Testing

- Write tests for all new features and bug fixes
- Use Django's testing framework
- Aim for high test coverage
- Test both positive and negative scenarios

```python
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Task

class TaskAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name='Test Project', owner=self.user)
        
    def test_create_task(self):
        """Test creating a task via the API"""
        url = reverse('task-list', kwargs={'project_id': self.project.id})
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'status': 'not_started'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.get().title, 'Test Task')
```

### Frontend Testing

- Use Jest for unit tests
- Use React Testing Library for component tests
- Test components in isolation
- Mock API calls and external dependencies

```jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TaskItem from './TaskItem';
import { updateTask } from '../api/tasks';

// Mock the API module
jest.mock('../api/tasks');

describe('TaskItem', () => {
  const mockTask = {
    id: '123',
    title: 'Test Task',
    status: 'in_progress'
  };
  
  it('renders task information correctly', () => {
    render(<TaskItem task={mockTask} />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });
  
  it('updates task status when complete button is clicked', async () => {
    updateTask.mockResolvedValue({ data: { ...mockTask, status: 'completed' } });
    
    render(<TaskItem task={mockTask} />);
    fireEvent.click(screen.getByText('Mark Complete'));
    
    await waitFor(() => {
      expect(updateTask).toHaveBeenCalledWith('123', { status: 'completed' });
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
  });
});
```

## Documentation Guidelines

Good documentation is crucial for the project. Please follow these guidelines:

- Update documentation for any feature changes
- Document all API endpoints
- Use clear, concise language
- Include examples where appropriate
- Keep README and other docs up to date
- Document configuration options and environment variables

For code documentation:
- Use docstrings for Python code
- Use JSDoc for JavaScript code
- Comment complex logic

## Issue Reporting Guidelines

When reporting issues, please include:

1. **Issue Description**: A clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment Information**:
   - Browser and version
   - Operating system
   - Backend/frontend versions
   - Any relevant environment variables
6. **Screenshots**: If applicable
7. **Suggested Solution**: If you have ideas on how to fix the issue

Use the issue templates provided in the repository when available.

## Security Vulnerability Reporting

If you discover a security vulnerability, please DO NOT open a public issue. Instead:

1. Email the project maintainers directly
2. Include a detailed description of the vulnerability
3. Provide steps to reproduce if possible
4. Wait for a response before disclosing publicly

We take security issues seriously and will work quickly to address them.

---

Thank you for contributing to the Project Management application! Your efforts help make this project better for everyone. 