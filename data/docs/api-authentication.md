# API: Authentication

The TaskFlow API uses API keys for authentication. Every request must
include a valid API key in the `Authorization` header.

## Base URL

```
https://api.taskflow.example.com/v1
```

All API endpoints are scoped under `/v1`. Future versions will be available
at `/v2`, `/v3`, etc., and old versions will remain available for at least
12 months after a new version is released.

## Generating an API key

1. Go to **Settings → Developer → API keys** in the web app
2. Click **Generate new key**
3. Give the key a descriptive name (e.g., "Zapier integration" or "Backup
   script")
4. Select the **scope** — see below
5. Click **Create**
6. Copy the key immediately — it is shown only once, and cannot be
   retrieved later

If you lose a key, you'll need to revoke it and create a new one.

## API key scopes

Each key can have one of three scopes:

- **Read-only** — `GET` requests only; cannot modify any data
- **Read/write** — `GET`, `POST`, `PATCH`, `DELETE` on resources the user
  has access to
- **Admin** — full access, including workspace settings and member
  management. Only workspace admins can create admin-scoped keys.

Use the narrowest scope that works for your use case. Read-only keys are
safer to store in automation tools.

## Authenticating a request

Include the API key as a Bearer token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer tf_live_abc123def456..." \
  https://api.taskflow.example.com/v1/tasks
```

Keys starting with `tf_live_` are production keys. Keys starting with
`tf_test_` are sandbox keys that work only against a test workspace.

## Example: Python

```python
import requests

API_KEY = "tf_live_abc123def456..."
headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.get(
    "https://api.taskflow.example.com/v1/tasks",
    headers=headers
)
print(response.json())
```

## Example: JavaScript (Node.js)

```javascript
const response = await fetch(
  "https://api.taskflow.example.com/v1/tasks",
  {
    headers: {
      "Authorization": `Bearer ${process.env.TASKFLOW_API_KEY}`
    }
  }
);
const data = await response.json();
```

## Revoking a key

Go to **Settings → Developer → API keys**, find the key, and click
**Revoke**. Revocation takes effect immediately — any further requests
using that key return `401 Unauthorized`.

Revoke a key immediately if:

- It was accidentally committed to a public repository
- A team member who had access leaves the organization
- You suspect it was exposed in any way

## Rate limits

API requests are rate-limited. See the "API Rate Limits" doc for details.

## OAuth

OAuth-based authentication is available for integrations that act on
behalf of other TaskFlow users. OAuth is currently in beta and available
only to Enterprise customers. Contact support@taskflow.example.com if you
need access.

## Frequently asked questions

**Can I have multiple API keys per user?**
Yes. There's no limit. We recommend one key per integration so you can
revoke them independently.

**Do API keys expire?**
No, API keys don't expire. But they can be revoked at any time.

**Can I see when a key was last used?**
Yes. The API keys page shows the last-used timestamp and IP address for
each key.

**Are API calls billed?**
No. API usage is included in all paid plans and doesn't count against any
user or task limit. Only rate limits apply.
