from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization
from projects.models import Project, ProjectMember, Board, Column
from tasks.models import Task, Comment, Label, TaskAttachment

User = get_user_model()

class TaskModelTests(TestCase):
    """Test cases for the Task model"""
    
    def setUp(self):
        # Create test user and organization
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            created_by=self.user
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            organization=self.organization,
            created_by=self.user
        )
        self.board = Board.objects.create(
            name='Test Board',
            project=self.project,
            created_by=self.user
        )
        self.column = Column.objects.create(
            name='Test Column',
            board=self.board,
            order=0,
            created_by=self.user
        )
        
    def test_task_creation(self):
        """Test creating a task"""
        task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            column=self.column,
            order=0,
            created_by=self.user
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'Test task description')
        self.assertEqual(task.column, self.column)
        self.assertEqual(task.created_by, self.user)
        
    def test_task_comment_creation(self):
        """Test adding a comment to a task"""
        task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            column=self.column,
            order=0,
            created_by=self.user
        )
        
        comment = Comment.objects.create(
            task=task,
            content='Test comment',
            created_by=self.user
        )
        
        self.assertEqual(comment.task, task)
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(comment.created_by, self.user)
        
    def test_task_label_creation(self):
        """Test creating a label"""
        label = Label.objects.create(
            name='Bug',
            color='#FF0000',
            project=self.project,
            created_by=self.user
        )
        
        self.assertEqual(label.name, 'Bug')
        self.assertEqual(label.color, '#FF0000')
        self.assertEqual(label.project, self.project)


class TaskAPITests(APITestCase):
    """Test cases for the Task API endpoints"""
    
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            created_by=self.user
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            organization=self.organization,
            created_by=self.user
        )
        
        # Add user as project member
        ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='admin'
        )
        
        # Create test board
        self.board = Board.objects.create(
            name='Test Board',
            project=self.project,
            created_by=self.user
        )
        
        # Create test column
        self.column = Column.objects.create(
            name='Test Column',
            board=self.board,
            order=0,
            created_by=self.user
        )
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            column=self.column,
            order=0,
            created_by=self.user
        )
        
    def test_get_tasks(self):
        """Test retrieving tasks list"""
        url = reverse('task-list', kwargs={'column_id': self.column.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Task')
        
    def test_create_task(self):
        """Test creating a new task"""
        url = reverse('task-list', kwargs={'column_id': self.column.id})
        data = {
            'title': 'New Task',
            'description': 'New task description',
            'order': 1
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Task')
        self.assertEqual(response.data['description'], 'New task description')
        
    def test_get_task_detail(self):
        """Test retrieving a specific task"""
        url = reverse('task-detail', kwargs={
            'column_id': self.column.id,
            'pk': self.task.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Task')
        
    def test_update_task(self):
        """Test updating a task"""
        url = reverse('task-detail', kwargs={
            'column_id': self.column.id,
            'pk': self.task.id
        })
        
        data = {
            'title': 'Updated Task',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['description'], 'Updated description')
        
    def test_delete_task(self):
        """Test deleting a task"""
        url = reverse('task-detail', kwargs={
            'column_id': self.column.id,
            'pk': self.task.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)
        
    def test_add_comment(self):
        """Test adding a comment to a task"""
        url = reverse('task-comments', kwargs={
            'task_id': self.task.id
        })
        
        data = {
            'content': 'Test comment'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test comment')
        self.assertEqual(Comment.objects.count(), 1)
