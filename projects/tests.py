from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization
from projects.models import Project, ProjectMember, Board, Column

User = get_user_model()

class ProjectModelTests(TestCase):
    """Test cases for the Project model"""
    
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
        
    def test_project_creation(self):
        """Test creating a project"""
        project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            organization=self.organization,
            created_by=self.user
        )
        
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.description, 'Test project description')
        self.assertEqual(project.organization, self.organization)
        self.assertEqual(project.created_by, self.user)
        
    def test_project_member_creation(self):
        """Test adding a member to a project"""
        project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            organization=self.organization,
            created_by=self.user
        )
        
        member = ProjectMember.objects.create(
            project=project,
            user=self.user,
            role='admin'
        )
        
        self.assertEqual(member.project, project)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, 'admin')


class ProjectAPITests(APITestCase):
    """Test cases for the Project API endpoints"""
    
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
        
    def test_get_projects(self):
        """Test retrieving projects list"""
        url = reverse('project-list', kwargs={'organization_id': self.organization.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Project')
        
    def test_create_project(self):
        """Test creating a new project"""
        url = reverse('project-list', kwargs={'organization_id': self.organization.id})
        data = {
            'name': 'New Project',
            'description': 'New project description',
            'is_public': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Project')
        self.assertEqual(response.data['description'], 'New project description')
        
    def test_get_project_detail(self):
        """Test retrieving a specific project"""
        url = reverse('project-detail', kwargs={
            'organization_id': self.organization.id,
            'pk': self.project.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')
        
    def test_update_project(self):
        """Test updating a project"""
        url = reverse('project-detail', kwargs={
            'organization_id': self.organization.id,
            'pk': self.project.id
        })
        
        data = {
            'name': 'Updated Project',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Project')
        self.assertEqual(response.data['description'], 'Updated description')
        
    def test_delete_project(self):
        """Test deleting a project"""
        url = reverse('project-detail', kwargs={
            'organization_id': self.organization.id,
            'pk': self.project.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)


class BoardAPITests(APITestCase):
    """Test cases for the Board API endpoints"""
    
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
        
    def test_get_boards(self):
        """Test retrieving boards list"""
        url = reverse('board-list', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Board')
        
    def test_create_board(self):
        """Test creating a new board"""
        url = reverse('board-list', kwargs={'project_id': self.project.id})
        data = {
            'name': 'New Board',
            'description': 'New board description'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Board')
        self.assertEqual(response.data['description'], 'New board description')
