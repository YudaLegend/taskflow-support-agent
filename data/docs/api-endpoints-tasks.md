# API: Tasks Endpoints

This doc describes the endpoints for creating, reading, updating, and
deleting tasks via the TaskFlow API.

Base URL: `https://api.taskflow.example.com/v1`

All endpoints require authentication. See the API Authentication doc.

## Task object

A task is returned as a JSON object with the following fields:

```json
{
  "id": "TF-1234",
  "project_id": "proj_abc123",
  "title": "Write homepage copy",
  "description": "Draft the copy for the new homepage hero section.",
  "status": "in_progress",
  "priority": "high",
  "assignee_id": "user_def456",
  "due_date": "2026-05-15",
  "start_date": "2026-05-10",
  "labels": ["design", "website"],
  "parent_task_id": null,
  "created_at": "2026-05-01T10:30:00Z",
  "updated_at": "2026-05-11T14:22:00Z",
  "completed_at": null
}
```

## GET /tasks

List tasks in a project.

**Query parameters:**

| Parameter    | Type    | Required | Description                                      |
|--------------|---------|----------|--------------------------------------------------|
| `project_id` | string  | yes      | The project to list tasks from                   |
| `status`     | string  | no       | Filter by status: `todo`, `in_progress`, `in_review`, `done` |
| `assignee_id`| string  | no       | Filter by assignee                               |
| `limit`      | integer | no       | Max results to return (default 50, max 200)     |
| `cursor`     | string  | no       | Pagination cursor from a previous response      |

**Example request:**

```bash
curl -H "Authorization: Bearer tf_live_..." \
  "https://api.taskflow.example.com/v1/tasks?project_id=proj_abc123&status=in_progress"
```

**Example response:**

```json
{
  "tasks": [
    { "id": "TF-1234", "title": "...", ... },
    { "id": "TF-1235", "title": "...", ... }
  ],
  "next_cursor": "cursor_xyz789"
}
```

If `next_cursor` is present, more results are available. Pass it as the
`cursor` parameter in the next request.

## GET /tasks/{id}

Get a single task by ID.

**Example request:**

```bash
curl -H "Authorization: Bearer tf_live_..." \
  https://api.taskflow.example.com/v1/tasks/TF-1234
```

**Example response:** a single task object (see above).

**Errors:**

- `404 Not Found` — task doesn't exist or you don't have access

## POST /tasks

Create a new task.

**Required fields:**

- `project_id` (string)
- `title` (string)

**Optional fields:**

- `description` (string, Markdown)
- `status` (string, default `todo`)
- `priority` (string: `low`, `medium`, `high`, `urgent`, default `medium`)
- `assignee_id` (string)
- `due_date` (ISO 8601 date)
- `start_date` (ISO 8601 date)
- `labels` (array of strings)
- `parent_task_id` (string, for creating subtasks)

**Example request:**

```bash
curl -X POST \
  -H "Authorization: Bearer tf_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_abc123",
    "title": "Fix login bug",
    "priority": "high",
    "assignee_id": "user_def456"
  }' \
  https://api.taskflow.example.com/v1/tasks
```

**Example response:** the newly created task object with status `201 Created`.

## PATCH /tasks/{id}

Update an existing task. Include only the fields you want to change.

**Example request:**

```bash
curl -X PATCH \
  -H "Authorization: Bearer tf_live_..." \
  -H "Content-Type: application/json" \
  -d '{ "status": "done" }' \
  https://api.taskflow.example.com/v1/tasks/TF-1234
```

**Example response:** the updated task object.

**Errors:**

- `404 Not Found` — task doesn't exist
- `403 Forbidden` — you don't have edit access

## DELETE /tasks/{id}

Delete a task. This is permanent — deleted tasks cannot be restored via
the API.

**Example request:**

```bash
curl -X DELETE \
  -H "Authorization: Bearer tf_live_..." \
  https://api.taskflow.example.com/v1/tasks/TF-1234
```

**Example response:** `204 No Content` on success.

## Bulk operations

To update or delete many tasks at once, use the bulk endpoints:

- `POST /tasks/bulk` — create up to 100 tasks in one request
- `PATCH /tasks/bulk` — update up to 100 tasks in one request
- `DELETE /tasks/bulk` — delete up to 100 tasks in one request

Bulk requests return partial success — individual task failures don't
fail the whole request.

## Error responses

All errors follow this format:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "project_id is required"
  }
}
```

Common error codes:

- `invalid_request` (400) — missing or invalid parameters
- `unauthorized` (401) — missing or invalid API key
- `forbidden` (403) — authenticated but not allowed
- `not_found` (404) — resource doesn't exist
- `rate_limited` (429) — too many requests, see rate limits doc
- `internal_error` (500) — our bug, please retry

## Frequently asked questions

**Can I subscribe to real-time task updates?**
Yes, use webhooks. See the integrations doc.

**How do I filter tasks by label?**
Use the `labels` query parameter with a comma-separated list:
`?labels=bug,urgent`. Matching is inclusive (OR).

**Can I include comments in the task response?**
Not in the standard response. Use `GET /tasks/{id}/comments` to fetch
comments separately.
