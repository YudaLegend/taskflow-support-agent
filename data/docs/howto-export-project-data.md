# How to Export Project Data

TaskFlow lets you export your project data at any time, for backup,
reporting, or migration purposes.

## Before you start

- You need at least **Editor** role on the project you want to export
- For full workspace exports, you must be a workspace admin

## Exporting a single project

### 1. Open the project

Navigate to the project you want to export.

### 2. Open the export menu

Click the **···** button in the top-right corner of the project, then
select **Export**.

### 3. Choose an export format

- **CSV** — a spreadsheet-friendly format with one row per task. Good for
  Excel, Google Sheets, or import into other tools.
- **JSON** — full data with all task properties, comments metadata, and
  relationships. Good for developers and API users.
- **PDF** — a printable summary of the project. Good for reports and
  archiving.

### 4. Choose what to include

- **All tasks** — exports everything in the project
- **Filtered view** — exports only tasks matching your current filters (for
  example, "only tasks assigned to me")
- **Date range** — exports only tasks created or updated within the range

### 5. Click Export

The file downloads immediately for small projects. For large projects
(1,000+ tasks) the export is generated in the background and emailed to you
within a few minutes.

## What's included in a CSV export

Each row is one task, with columns:

- Task ID
- Title
- Description
- Status
- Priority
- Assignee email
- Due date
- Start date
- Labels (comma-separated)
- Created at
- Completed at
- Parent task ID (for subtasks)

Comments and attachments are **not** included in CSV exports — use JSON or
the API for those.

## What's included in a JSON export

JSON exports include everything CSV has, plus:

- Comment metadata (author, timestamp, text) — but not attached files
- Full timestamps for all status changes
- Custom field values (Business and Enterprise plans)
- Label colors and descriptions

## Exporting an entire workspace

Workspace admins can export all projects at once:

1. Go to **Settings → Data → Export workspace**
2. Choose format (ZIP of CSVs, or a single JSON file)
3. Click **Request export**

Workspace exports are always generated in the background and emailed to
the admin's address. Expect it to take 5–30 minutes depending on workspace
size.

## Automated / scheduled exports

To export data on a schedule, use one of these options:

- **Zapier** — set up a Zap that triggers "every day at 6 AM" and calls the
  TaskFlow API to fetch tasks
- **Webhooks** — stream task events to your own storage in real time
- **API** — write a script that calls `GET /tasks` periodically

See the API documentation for examples.

## Tips

- **Schedule backups.** Even though TaskFlow backs up your data
  automatically, having your own copy is good practice.
- **Filter before exporting.** Exporting a filtered view is much faster
  than exporting everything and filtering in Excel.
- **Use JSON for migrations.** If you're moving data between workspaces or
  tools, JSON preserves more information than CSV.

## Frequently asked questions

**Are attachments included in exports?**
No. Only task data is exported. To back up attachments, download them
individually or use the API.

**Can I import data back into TaskFlow?**
Yes. Go to **Settings → Data → Import** to import CSV or JSON files. Only
workspace admins can import.

**Is there a size limit on exports?**
No hard limit, but exports larger than 500 MB are split into multiple
files.

**How long is a background export link valid?**
Download links in export emails are valid for 7 days, then expire for
security reasons.
