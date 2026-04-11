# How to Connect Slack

Connecting TaskFlow to Slack lets you receive task updates in your Slack
channels and create tasks without leaving Slack.

## Before you start

- Your TaskFlow plan must be Pro or higher (Free does not support Slack)
- You must be a workspace admin in TaskFlow
- You must have permission to install apps in your Slack workspace (or ask
  your Slack admin to do it for you)

## Steps

### 1. Go to the integrations settings

In TaskFlow, click your workspace name in the top-left, then
**Settings → Integrations**. Find **Slack** in the list and click
**Connect**.

### 2. Authorize the Slack workspace

You'll be redirected to Slack. Choose the Slack workspace you want to
connect and review the permissions TaskFlow is requesting:

- Send messages to channels you approve
- Read basic info about your Slack workspace (to show channel names)
- Respond to slash commands

Click **Allow**.

### 3. Pick the default notification channel

Back in TaskFlow, choose a default Slack channel where system notifications
will go when no specific channel is set for a project. Most teams use
`#taskflow` or `#general`.

### 4. Configure per-project notifications (optional)

You can route notifications from specific projects to specific Slack
channels:

1. Open a project
2. Click **··· → Settings → Integrations → Slack**
3. Choose the channel for this project's notifications
4. Select which events should notify Slack:
   - Task created
   - Task completed
   - Task assigned
   - Comment added
   - Mention in a comment

### 5. Test it

Create a test task in the project you configured. Within a few seconds you
should see a message in the Slack channel you picked.

## Using the /taskflow slash command

Once connected, you can create tasks from any Slack channel:

```
/taskflow create "Fix login bug" #website-redesign
```

This creates a task called "Fix login bug" in the "Website Redesign"
project. You can also use:

```
/taskflow list            → show your open tasks
/taskflow assign @alice   → assign the current task to Alice
/taskflow done            → mark the last task you mentioned as done
```

## Rich task previews

When someone pastes a TaskFlow task link into Slack (e.g.,
`https://taskflow.example.com/tasks/TF-1234`), Slack automatically shows a
preview with the task title, assignee, status, and due date. Click the
preview to open the task in TaskFlow.

## Disconnecting Slack

To disconnect, go to **Settings → Integrations → Slack → Disconnect**.

**What happens when you disconnect:**

- Slack notifications stop immediately
- The `/taskflow` slash command stops working
- Existing task links in Slack still work but no longer show previews
- No task data is deleted

## Frequently asked questions

**Can I connect multiple Slack workspaces?**
Business and Enterprise plans can connect multiple Slack workspaces. Pro
plans are limited to one.

**Why am I not getting notifications in a private channel?**
TaskFlow needs to be invited to private channels manually. Type
`/invite @TaskFlow` in the private channel to add it.

**Can I customize the format of Slack messages?**
Business and Enterprise plans can customize message templates from
**Settings → Integrations → Slack → Templates**.

**Does the Slack integration work with Slack Enterprise Grid?**
Yes, but it must be connected at the individual workspace level, not at
the Grid level.
