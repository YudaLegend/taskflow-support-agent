# Integrations

TaskFlow connects to the tools your team already uses. Integrations are
managed from **Settings → Integrations** in the web app.

## Slack

Connect TaskFlow to any Slack workspace to receive task updates directly in
your channels.

**What you can do:**

- Get notified in a channel when tasks are created, completed, or commented on
- Use the `/taskflow` slash command to create tasks from Slack
- See rich task previews when pasting TaskFlow links into Slack
- Acknowledge @mentions from Slack without opening TaskFlow

**Available on:** Pro, Business, Enterprise
**Setup guide:** see "How to connect Slack".

## Google Drive

Attach Google Drive files to any task without downloading them first. The
attachment stays linked to the source file, so changes in Drive reflect in
TaskFlow automatically.

**What you can do:**

- Attach Docs, Sheets, Slides, and any Drive file to tasks
- See preview thumbnails inline
- Control access: viewers of the task can open the file only if they have
  Drive permissions

**Available on:** Pro, Business, Enterprise

## GitHub

Link TaskFlow tasks to GitHub issues and pull requests. When the linked PR
is merged, the task is automatically moved to "Done".

**What you can do:**

- Reference TaskFlow tasks in commit messages using `TF-1234` syntax
- See linked PR status on the task (open, merged, closed)
- Auto-close tasks when PRs merge
- Sync issue comments from GitHub into TaskFlow

**Available on:** Business, Enterprise only

## Zapier

Connect TaskFlow to 5,000+ other apps via Zapier. Popular use cases:

- Create a task when a new row is added to a Google Sheet
- Post to Discord when a task is marked Urgent
- Create a task from a new Typeform submission
- Email a customer when their support ticket is marked Done

**Triggers supported:** task created, task updated, task completed, comment
added, task assigned.

**Actions supported:** create task, update task, add comment, assign task.

**Available on:** Pro, Business, Enterprise

## Jira (Business and Enterprise)

Two-way sync with Jira projects. Useful for teams migrating from Jira or
teams where engineering uses Jira and other departments use TaskFlow.

**What you can do:**

- Mirror Jira issues as TaskFlow tasks
- Sync status changes in both directions
- Map Jira custom fields to TaskFlow task properties

**Available on:** Business, Enterprise

## Webhook integration

For anything not covered by a pre-built integration, TaskFlow can send
webhooks to any URL you choose whenever task events happen. See the API
documentation for webhook payload format and authentication.

## Frequently asked questions

**Do integrations count against my user limits?**
No. Integrations are system-level and don't consume user seats.

**Can I connect multiple Slack workspaces to one TaskFlow workspace?**
Yes, on the Business and Enterprise plans. Pro plans are limited to one
connected Slack workspace.

**What happens to attached Google Drive files if I revoke Drive access?**
Existing links become inaccessible but are not deleted. Re-authorizing
Drive restores access immediately.

**Is there an integration for Microsoft Teams?**
Microsoft Teams integration is on our roadmap but is not available yet.
In the meantime, you can use the Zapier integration as a workaround.
