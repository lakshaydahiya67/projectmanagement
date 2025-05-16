# API Documentation

This document provides detailed information about the Project Management API endpoints, request/response formats, and authentication.

## API Overview

The API follows RESTful principles and is organized around resources:

- **Authentication** - User registration, login, and token management
- **Users** - User profile management
- **Organizations** - Organization management
- **Projects** - Project management within organizations  
- **Tasks** - Task management within projects
- **Activity Logs** - Tracking user actions
- **Notifications** - User notifications

## Base URL

- Local Development: `http://localhost:8000/api/v1/`
- Docker: `http://localhost/api/v1/`
- Production: `https://yourdomain.com/api/v1/`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header for authenticated requests.

### Endpoints

#### Register a new user

```
POST /auth/users/
```

Request body:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response:
```json
{
  "id": "09bda9af-2d08-439b-911c-9449cdb5e659",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login (Get JWT token)

```
POST /auth/jwt/create/
```

Request body:
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Refresh token

```
POST /auth/jwt/refresh/
```

Request body:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Users

### Endpoints

#### Get current user

```
GET /users/me/
```

Response:
```json
{
  "id": "09bda9af-2d08-439b-911c-9449cdb5e659",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "avatar": null,
    "theme_preference": "light",
    "notification_preferences": {
      "email": true,
      "push": true
    }
  }
}
```

#### Update user profile

```
PATCH /users/me/
```

Request body:
```json
{
  "first_name": "Jonathan",
  "profile": {
    "theme_preference": "dark"
  }
}
```

Response:
```json
{
  "id": "09bda9af-2d08-439b-911c-9449cdb5e659",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "profile": {
    "avatar": null,
    "theme_preference": "dark",
    "notification_preferences": {
      "email": true,
      "push": true
    }
  }
}
```

## Organizations

### Endpoints

#### List organizations

```
GET /organizations/
```

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "description": "A fictional company",
      "logo": null,
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z",
      "member_count": 5
    }
  ]
}
```

#### Create organization

```
POST /organizations/
```

Request body:
```json
{
  "name": "New Company",
  "description": "My new company"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "New Company",
  "slug": "new-company",
  "description": "My new company",
  "logo": null,
  "created_at": "2025-01-02T12:00:00Z",
  "updated_at": "2025-01-02T12:00:00Z",
  "member_count": 1
}
```

#### Get organization

```
GET /organizations/{id}/
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corp",
  "slug": "acme-corp",
  "description": "A fictional company",
  "logo": null,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z",
  "member_count": 5,
  "members": [
    {
      "id": "09bda9af-2d08-439b-911c-9449cdb5e659",
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "admin"
    }
  ]
}
```

## Projects

### Endpoints

#### List organization projects

```
GET /organizations/{org_id}/projects/
```

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Website Redesign",
      "description": "Redesign company website",
      "organization": "550e8400-e29b-41d4-a716-446655440000",
      "status": "in_progress",
      "start_date": "2025-01-15",
      "end_date": "2025-03-15",
      "created_at": "2025-01-10T12:00:00Z",
      "updated_at": "2025-01-10T12:00:00Z"
    }
  ]
}
```

#### Create project

```
POST /organizations/{org_id}/projects/
```

Request body:
```json
{
  "name": "Mobile App",
  "description": "New mobile application",
  "start_date": "2025-02-01",
  "end_date": "2025-05-01"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "Mobile App",
  "description": "New mobile application",
  "organization": "550e8400-e29b-41d4-a716-446655440000",
  "status": "not_started",
  "start_date": "2025-02-01",
  "end_date": "2025-05-01",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

## Tasks

### Endpoints

#### List project tasks

```
GET /projects/{project_id}/tasks/
```

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "title": "Design homepage",
      "description": "Create mockups for homepage",
      "status": "in_progress",
      "priority": "high",
      "assignee": "09bda9af-2d08-439b-911c-9449cdb5e659",
      "due_date": "2025-02-01",
      "created_at": "2025-01-20T12:00:00Z",
      "updated_at": "2025-01-20T12:00:00Z"
    }
  ]
}
```

#### Create task

```
POST /projects/{project_id}/tasks/
```

Request body:
```json
{
  "title": "Implement login page",
  "description": "Create login form with validation",
  "priority": "medium",
  "due_date": "2025-02-15"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "title": "Implement login page",
  "description": "Create login form with validation",
  "status": "not_started",
  "priority": "medium",
  "assignee": null,
  "due_date": "2025-02-15",
  "created_at": "2025-01-21T12:00:00Z",
  "updated_at": "2025-01-21T12:00:00Z"
}
```

#### Update task

```
PATCH /tasks/{task_id}/
```

Request body:
```json
{
  "status": "completed",
  "assignee": "09bda9af-2d08-439b-911c-9449cdb5e659"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "title": "Implement login page",
  "description": "Create login form with validation",
  "status": "completed",
  "priority": "medium",
  "assignee": "09bda9af-2d08-439b-911c-9449cdb5e659",
  "due_date": "2025-02-15",
  "created_at": "2025-01-21T12:00:00Z",
  "updated_at": "2025-01-22T12:00:00Z"
}
```

## Activity Logs

### Endpoints

#### Get activity logs

```
GET /activity-logs/
```

Query parameters:
- `content_type` - Filter by content type (e.g., "project", "task")
- `object_id` - Filter by object ID
- `action` - Filter by action (e.g., "CREATED", "UPDATED")
- `user` - Filter by user ID
- `date_from` - Filter by date (format: YYYY-MM-DD)
- `date_to` - Filter by date (format: YYYY-MM-DD)

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "user": {
        "id": "09bda9af-2d08-439b-911c-9449cdb5e659",
        "username": "johndoe"
      },
      "content_type": "task",
      "object_id": "550e8400-e29b-41d4-a716-446655440005",
      "action": "UPDATED",
      "description": "Task status changed to completed",
      "timestamp": "2025-01-22T12:00:00Z",
      "details": {
        "changes": {
          "status": {
            "old": "not_started",
            "new": "completed"
          },
          "assignee": {
            "old": null,
            "new": "09bda9af-2d08-439b-911c-9449cdb5e659"
          }
        }
      }
    }
  ]
}
```

## Notifications

### Endpoints

#### List notifications

```
GET /notifications/
```

Query parameters:
- `read` - Filter by read status (true/false)

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "user": "09bda9af-2d08-439b-911c-9449cdb5e659",
      "type": "task_assigned",
      "title": "Task assigned to you",
      "message": "You have been assigned to task 'Implement login page'",
      "related_object_type": "task",
      "related_object_id": "550e8400-e29b-41d4-a716-446655440005",
      "read": false,
      "created_at": "2025-01-22T12:00:00Z"
    }
  ]
}
```

#### Mark notification as read

```
PATCH /notifications/{notification_id}/
```

Request body:
```json
{
  "read": true
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440007",
  "user": "09bda9af-2d08-439b-911c-9449cdb5e659",
  "type": "task_assigned",
  "title": "Task assigned to you",
  "message": "You have been assigned to task 'Implement login page'",
  "related_object_type": "task",
  "related_object_id": "550e8400-e29b-41d4-a716-446655440005",
  "read": true,
  "created_at": "2025-01-22T12:00:00Z"
}
```

## Error Responses

The API uses standard HTTP status codes to indicate the success or failure of requests.

### Common Error Codes

- `400 Bad Request` - The request was invalid or malformed
- `401 Unauthorized` - Authentication is required or failed
- `403 Forbidden` - The authenticated user does not have permission
- `404 Not Found` - The requested resource was not found
- `500 Internal Server Error` - Server-side error

### Error Response Format

```json
{
  "detail": "Error message"
}
```

or for field-specific errors:

```json
{
  "field_name": [
    "Error message"
  ]
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. The current limits are:

- Unauthenticated requests: 20 requests per minute
- Authenticated requests: 60 requests per minute

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

## Interactive API Documentation

For interactive documentation and API testing, the following tools are available:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

These tools allow you to explore all available endpoints, view request/response schemas, and test API calls directly from your browser. 