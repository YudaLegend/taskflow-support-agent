# Comments and Mentions

TaskFlow lets you have threaded discussions directly on any task. Comments
keep conversation close to the work instead of scattered across email and
chat.

## Adding a comment

Open any task and scroll to the **Comments** section at the bottom. Type
your message and press **Cmd/Ctrl + Enter** to post it, or click **Post**.

Comments support:

- **Markdown formatting** — bold, italic, lists, code blocks, links
- **File attachments** — drag and drop or click the paperclip icon
- **Emoji reactions** — click the smiley icon next to any comment
- **Inline image previews** — pasted screenshots render inline

## Mentioning teammates

Type `@` followed by a teammate's name to open the mention picker. Select
their name to insert a mention. Mentioned users receive a notification
immediately, even if they aren't assigned to the task.

You can also mention:

- `@project` — notifies all members of the current project
- `@everyone` — notifies the entire workspace (Business and Enterprise only,
  to prevent notification spam in large organizations)

## Editing and deleting comments

You can edit or delete your own comments at any time using the `···` menu on
the comment. Edited comments show an "(edited)" label.

Workspace admins on the Business and Enterprise plans can delete any
comment, including ones posted by other users. This is useful for removing
accidentally-shared sensitive information.

## Comment notifications

You receive a notification when:

- Someone mentions you with `@yourname`
- Someone replies to a thread you started
- Someone comments on a task you're assigned to
- Someone comments on a task you're watching

You can customize which of these trigger notifications from
**Settings → Notifications**.

## Resolving threads

Comments can be organized into threads. Once a conversation is done, click
**Resolve** at the top of the thread to collapse it. Resolved threads are
hidden by default but can be shown again with the "Show resolved" toggle.

## Frequently asked questions

**Can I mention someone who isn't in the project?**
Only if they are a member of the workspace. If they are not, you can
invite them directly from the mention picker and they will be added to the
project automatically.

**Can I react with custom emojis?**
Custom emoji reactions are available on the Business and Enterprise plans.
Free and Pro plans have access to the standard Unicode emoji set.

**Are comments included in CSV exports?**
No. Comments are considered discussion content and are not included in CSV
exports. To export comments, use the TaskFlow API.

**Can I format code inside a comment?**
Yes. Wrap inline code in backticks (`` `like this` ``) or use triple
backticks for a multi-line code block with syntax highlighting.
