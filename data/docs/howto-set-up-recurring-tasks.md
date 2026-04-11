# How to Set Up Recurring Tasks

Recurring tasks automatically regenerate on a schedule you choose — perfect
for weekly standups, monthly reports, or daily check-ins.

## Before you start

- You need edit access to the project where you want the recurring task
- Recurring tasks are available on all plans

## Creating a recurring task

### 1. Create a task as usual

Click **+ New task** and fill in the title, description, assignee, and
priority.

### 2. Open the recurrence settings

In the task creation dialog, click **Does not repeat** near the due date
field. A recurrence menu appears.

### 3. Choose a recurrence pattern

TaskFlow supports these patterns out of the box:

- **Daily** — every N days
- **Weekly** — every N weeks, on specific days of the week
- **Monthly** — every N months, on a specific date or day (e.g., "the first
  Monday")
- **Yearly** — every N years on a specific date
- **Custom** — combine any of the above

### 4. Set an end condition (optional)

By default, recurring tasks continue forever. You can set an end:

- **After N occurrences** — stops after that many tasks have been created
- **On a specific date** — stops creating new tasks after that date
- **Never** — the default

### 5. Save the task

Click **Save**. The first task appears immediately. The next occurrence is
automatically created when the current one is completed or when its due
date passes.

## How recurring tasks behave

**When the current task is completed:**
A new task is created immediately with the next due date in the pattern.

**When the current task is overdue:**
A new task is still created on schedule — overdue tasks don't block future
recurrences.

**When you edit a recurring task:**
Changes apply only to the current occurrence by default. To change all
future occurrences, click **··· → Edit all future occurrences**.

**When you delete a recurring task:**
You're asked whether to delete just the current occurrence or the entire
recurring series.

## Example: weekly team standup

1. Create a task called "Weekly team standup"
2. Assign it to the team lead
3. Set the due date to next Monday at 9:00 AM
4. Click **Does not repeat → Weekly → Every 1 week on Monday**
5. Leave "End" as Never
6. Save

Every Monday, a new standup task will appear automatically.

## Example: monthly report

1. Create a task called "Monthly finance report"
2. Set the due date to the first of next month
3. Click **Does not repeat → Monthly → On the 1st of every month**
4. Set end: **After 12 occurrences** (one year's worth)
5. Save

## Tips

- **Don't overuse recurrence.** If a task needs to happen every day, it's
  often better to use a checklist inside a single task instead of creating
  365 duplicates.
- **Combine with labels.** Tag all recurring tasks with a "recurring" label
  so you can filter them out of busy Kanban boards.
- **Review monthly.** Recurring tasks can pile up if you miss a few —
  review them at the start of each month to catch any that slipped.

## Frequently asked questions

**Can a subtask be recurring?**
No. Only top-level tasks can be set to recur.

**What happens to recurring tasks when I delete the project?**
The entire recurring series stops. Deleting a project removes all its
tasks, including pending future occurrences.

**Can different assignees rotate on a recurring task?**
Not directly. A recurring task keeps the same assignee each time. For
rotating assignment, use a Zapier integration with a custom rule.

**Do recurring tasks count toward my task limits?**
All plans have unlimited tasks, so no.
