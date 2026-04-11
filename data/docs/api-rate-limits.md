# API: Rate Limits

The TaskFlow API enforces rate limits to protect service stability. Limits
are applied per API key.

## Rate limit tiers

| Plan       | Requests / minute | Requests / day |
|------------|-------------------|----------------|
| Free       | 30                | 1,000          |
| Pro        | 120               | 10,000         |
| Business   | 300               | 50,000         |
| Enterprise | 1,000             | 500,000        |

Rate limits are enforced per API key, not per workspace. If you have
multiple keys, each has its own limit.

## Rate limit headers

Every API response includes three headers:

- `X-RateLimit-Limit` — your limit for the current window
- `X-RateLimit-Remaining` — how many requests you have left
- `X-RateLimit-Reset` — UNIX timestamp when the window resets

**Example:**

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1747000800
```

Use these to pace your requests and avoid hitting the limit.

## When you exceed the limit

If you go over the limit, TaskFlow returns `429 Too Many Requests`:

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Rate limit exceeded. Retry after 42 seconds."
  }
}
```

The response includes a `Retry-After` header indicating how many seconds
to wait before retrying.

## Best practices

### Use exponential backoff

When you hit a rate limit, don't immediately retry. Use exponential
backoff:

```python
import time
import requests

def call_api_with_retry(url, headers, max_retries=5):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code != 429:
            return response
        retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
        time.sleep(retry_after)
    raise Exception("Max retries exceeded")
```

### Batch requests when possible

Use bulk endpoints (`POST /tasks/bulk`, `PATCH /tasks/bulk`, etc.) to do
more work with fewer requests. A bulk request of 100 tasks counts as a
single request against your rate limit.

### Cache data that doesn't change often

If your integration reads the same data repeatedly, cache it locally and
refresh only when needed. Most workspace metadata (projects, labels,
members) changes rarely.

### Use webhooks instead of polling

Instead of polling the API every minute to check for changes, subscribe to
webhooks. Webhooks push updates to you in real time and don't count
against rate limits.

## Upgrading your rate limit

If you consistently hit rate limits on your current plan, consider:

1. **Upgrading your plan** — higher plans have higher limits
2. **Optimizing your integration** — use bulk endpoints, webhooks, caching
3. **Contacting sales** — Enterprise customers can negotiate custom rate
   limits for high-volume use cases

## Rate limits for specific endpoints

A few endpoints have their own lower limits because they're expensive:

- `GET /search` — 10 requests/minute on all plans
- `POST /tasks/bulk` — 5 requests/minute on all plans
- `GET /workspace/export` — 1 request/hour on all plans

These limits are in addition to the overall per-minute limit.

## Frequently asked questions

**Do rate limits apply to the web app?**
No. Rate limits only apply to API requests using an API key. Interactive
use of the web and mobile apps is not rate-limited.

**What happens if I'm rate-limited during a Zapier Zap run?**
Zapier automatically retries 429 responses with backoff. You may see
delayed Zaps but data won't be lost.

**Are rate limits reset instantly at midnight?**
Per-minute limits roll on a sliding 60-second window. Per-day limits reset
at 00:00 UTC.

**How do I monitor my usage?**
Go to **Settings → Developer → API usage** to see request counts per key
over the last 30 days.
