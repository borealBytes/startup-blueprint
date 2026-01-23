# API Documentation

## Overview

This document provides complete API endpoint documentation for the Startup Blueprint application.

## Base URL

```
Production: https://startup-blueprint.pages.dev
Development: http://localhost:8787
```

## Authentication

Currently, the API does not require authentication. Future versions will implement token-based authentication.

## Endpoints

### Health Check

**GET /**

Returns application health status.

**Response:**
```json
{
  "status": "ok",
  "message": "Startup Blueprint API is running",
  "timestamp": "2026-01-23T18:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### Create Task

**POST /api/tasks**

Creates a new task in the database.

**Request Body:**
```json
{
  "title": "Complete API documentation",
  "description": "Write comprehensive API docs for all endpoints",
  "status": "pending",
  "priority": "high"
}
```

**Parameters:**
- `title` (string, required) - Task title (max 255 characters)
- `description` (string, optional) - Detailed task description
- `status` (string, optional) - One of: pending, in_progress, completed. Default: pending
- `priority` (string, optional) - One of: low, medium, high. Default: medium

**Response:**
```json
{
  "id": 1,
  "title": "Complete API documentation",
  "description": "Write comprehensive API docs for all endpoints",
  "status": "pending",
  "priority": "high",
  "created_at": "2026-01-23T18:00:00.000Z",
  "updated_at": "2026-01-23T18:00:00.000Z"
}
```

**Status Codes:**
- `201 Created` - Task created successfully
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Database error

---

### Get All Tasks

**GET /api/tasks**

Retrieves all tasks from the database.

**Query Parameters:**
- `status` (string, optional) - Filter by status: pending, in_progress, completed
- `priority` (string, optional) - Filter by priority: low, medium, high
- `limit` (number, optional) - Maximum number of tasks to return (default: 100, max: 1000)
- `offset` (number, optional) - Number of tasks to skip for pagination (default: 0)

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Complete API documentation",
      "description": "Write comprehensive API docs for all endpoints",
      "status": "in_progress",
      "priority": "high",
      "created_at": "2026-01-23T18:00:00.000Z",
      "updated_at": "2026-01-23T18:15:00.000Z"
    },
    {
      "id": 2,
      "title": "Fix database migrations",
      "description": null,
      "status": "completed",
      "priority": "medium",
      "created_at": "2026-01-22T10:30:00.000Z",
      "updated_at": "2026-01-23T09:45:00.000Z"
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

**Status Codes:**
- `200 OK` - Tasks retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `500 Internal Server Error` - Database error

---

### Get Task by ID

**GET /api/tasks/:id**

Retrieves a specific task by ID.

**Path Parameters:**
- `id` (number, required) - Task ID

**Response:**
```json
{
  "id": 1,
  "title": "Complete API documentation",
  "description": "Write comprehensive API docs for all endpoints",
  "status": "in_progress",
  "priority": "high",
  "created_at": "2026-01-23T18:00:00.000Z",
  "updated_at": "2026-01-23T18:15:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Task found
- `404 Not Found` - Task with specified ID does not exist
- `500 Internal Server Error` - Database error

---

### Update Task

**PUT /api/tasks/:id**

Updates an existing task.

**Path Parameters:**
- `id` (number, required) - Task ID

**Request Body:**
```json
{
  "title": "Complete API documentation - UPDATED",
  "description": "Write comprehensive API docs for all endpoints including examples",
  "status": "completed",
  "priority": "high"
}
```

**Parameters:**
All fields are optional. Only provided fields will be updated.
- `title` (string, optional) - Task title (max 255 characters)
- `description` (string, optional) - Detailed task description
- `status` (string, optional) - One of: pending, in_progress, completed
- `priority` (string, optional) - One of: low, medium, high

**Response:**
```json
{
  "id": 1,
  "title": "Complete API documentation - UPDATED",
  "description": "Write comprehensive API docs for all endpoints including examples",
  "status": "completed",
  "priority": "high",
  "created_at": "2026-01-23T18:00:00.000Z",
  "updated_at": "2026-01-23T18:30:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Task updated successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Task with specified ID does not exist
- `500 Internal Server Error` - Database error

---

### Delete Task

**DELETE /api/tasks/:id**

Deletes a task from the database.

**Path Parameters:**
- `id` (number, required) - Task ID

**Response:**
```json
{
  "success": true,
  "message": "Task deleted successfully",
  "id": 1
}
```

**Status Codes:**
- `200 OK` - Task deleted successfully
- `404 Not Found` - Task with specified ID does not exist
- `500 Internal Server Error` - Database error

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description",
  "details": "Additional error details if available",
  "timestamp": "2026-01-23T18:00:00.000Z"
}
```

## Rate Limiting

**Current:** No rate limiting implemented.

**Future:** Rate limiting will be implemented with the following limits:
- 1000 requests per hour per IP address
- 100 requests per minute per IP address

When rate limited, you'll receive:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

## Webhooks (Future)

Future versions will support webhooks for task events:
- `task.created` - Triggered when a new task is created
- `task.updated` - Triggered when a task is updated
- `task.completed` - Triggered when a task status changes to completed
- `task.deleted` - Triggered when a task is deleted

## Database Schema

See [MIGRATIONS.md](./MIGRATIONS.md) for complete database schema and migration guide.

## Example Usage

### cURL Examples

**Create a task:**
```bash
curl -X POST https://startup-blueprint.pages.dev/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "This is a test task",
    "status": "pending",
    "priority": "medium"
  }'
```

**Get all tasks:**
```bash
curl https://startup-blueprint.pages.dev/api/tasks
```

**Update a task:**
```bash
curl -X PUT https://startup-blueprint.pages.dev/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

**Delete a task:**
```bash
curl -X DELETE https://startup-blueprint.pages.dev/api/tasks/1
```

### JavaScript/Fetch Examples

**Create a task:**
```javascript
const response = await fetch('https://startup-blueprint.pages.dev/api/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Test Task',
    description: 'This is a test task',
    status: 'pending',
    priority: 'medium'
  })
});

const task = await response.json();
console.log('Created task:', task);
```

**Get all tasks:**
```javascript
const response = await fetch('https://startup-blueprint.pages.dev/api/tasks');
const data = await response.json();
console.log('Tasks:', data.tasks);
```

## Support

For questions or issues, please:
- Open an issue on GitHub: [startup-blueprint/issues](https://github.com/borealBytes/startup-blueprint/issues)
- Contact: support@startup-blueprint.com

## Changelog

### v1.0.0 (2026-01-23)
- Initial API release
- CRUD operations for tasks
- SQLite/D1 database integration
