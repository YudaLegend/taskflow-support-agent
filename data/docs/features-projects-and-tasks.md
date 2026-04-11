# Projects and Tasks

Projects and tasks are the core building blocks of TaskFlow. A project is a
container for related work, and tasks are the individual units of work inside
that project.

## Projects

A project groups together everything related to a single initiative — for
example, "Website Redesign" or "Q2 Marketing Campaign".

Each project has:

- A **name** and optional **description**
- A **color** and **icon** for quick visual identification
- A set of **members** with defined roles
- A **default view** (Kanban, List, Calendar, or Timeline)
- An optional **deadline**

### Project visibility

Projects can be either:

- **Private** — only invited members can see the project. Private projects
  are available on the Business and Enterprise plans.
- **Team** — visible to everyone in your workspace. Available on all plans.

### Project limits per plan

| Plan       | Active projects       |
|------------|-----------------------|
| Free       | Up to 3               |
| Pro        | Unlimited             |
| Business   | Unlimited             |
| Enterprise | Unlimited             |

## Tasks

A task is a single unit of work inside a project. You can create a task by
clicking the **+ New task** button on any project view or by pressing `N`
on your keyboard.

Each task has the following properties:

- **Title** (required)
- **Description** — supports Markdown formatting
- **Assignee** — one team member responsible for the task
- **Due date** and optional **start date**
- **Priority** — Low, Medium, High, or Urgent
- **Labels** — custom tags for filtering (e.g., "bug", "design", "blocked")
- **Status** — To Do, In Progress, In Review, or Done
- **Attachments** — up to 100 MB per file on paid plans, 10 MB on Free

### Subtasks

Each task can contain subtasks. TaskFlow supports **up to three levels of
nesting** (task → subtask → sub-subtask). Going deeper than that usually
means the work should be broken into separate tasks.

Subtasks inherit the parent task's project but can have their own assignees,
due dates, and priorities.

## Frequently asked questions

**Can I move a task between projects?**
Yes. Open the task, click the project name at the top, and select a different
project from the dropdown. All subtasks move with it.

**Can a task have more than one assignee?**
No. TaskFlow intentionally limits tasks to a single assignee to keep
accountability clear. If multiple people need to collaborate, use @mentions
in comments or create subtasks for each person.

**What happens to a task when its due date passes?**
The task is marked as overdue and highlighted in red on all views. Overdue
tasks also appear in the assignee's daily digest email.

**Is there a limit to how many tasks a project can have?**
No. All plans allow unlimited tasks per project.
