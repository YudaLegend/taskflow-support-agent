# How to Invite Team Members

This guide shows you how to invite people to your TaskFlow workspace and to
specific projects, and explains the different roles available.

## Before you start

- You must be a workspace admin or project member with permission to invite
- Your plan must support the number of members you want to add (Free is
  limited to 2, all paid plans are unlimited)

## Inviting at the workspace level

Workspace members can be added to any project inside the workspace.

1. Click your workspace name in the top-left, then **Settings**
2. Go to **Members → Invite people**
3. Enter one or more email addresses (separated by commas)
4. Select a **workspace role** (see roles below)
5. Optionally, add a personal message
6. Click **Send invitations**

Each person will receive an email with a link to join. Invitation links are
valid for 7 days.

## Inviting at the project level

If you only want to give someone access to a specific project (not the
whole workspace), you can invite them directly from the project.

1. Open the project
2. Click the **Members** icon in the top-right corner
3. Click **Add members**
4. Search for existing workspace members, or enter an email to invite a
   new person
5. Select a **project role**
6. Click **Add**

## Workspace roles

- **Admin** — can manage billing, add/remove members, change workspace
  settings, and has access to every project
- **Member** — can be invited to projects, create new projects, and
  collaborate normally
- **Guest** (Business and Enterprise only) — can only see projects they're
  explicitly invited to, cannot create new projects

## Project roles

- **Owner** — full control of the project, including deleting it
- **Editor** — can create, edit, and complete tasks; can comment
- **Commenter** — can view tasks and add comments but cannot edit
- **Viewer** — read-only access

A single project can have multiple owners. Transferring ownership doesn't
remove the original owner unless you choose to.

## Managing pending invitations

Go to **Settings → Members → Pending** to see invitations that haven't been
accepted yet. You can resend or revoke any pending invitation from this
page.

## Removing a member

1. Go to **Settings → Members**
2. Find the person in the list
3. Click the **···** menu next to their name
4. Select **Remove from workspace**

When you remove someone:

- They immediately lose access to all projects in the workspace
- Tasks they created stay in place
- Tasks assigned to them become unassigned
- Their comments remain visible

## Tips

- **Use Guest accounts** (Business+) for clients or external collaborators
  who should only see one project.
- **Review members quarterly.** If you're on a paid plan, you're billed per
  member — removing inactive members saves money.
- **Use the API** for bulk member management if you're onboarding many
  people at once.

## Frequently asked questions

**Do invited members count toward my plan's user limit?**
Yes, starting from the moment they accept the invitation. Pending
invitations don't count until accepted.

**Can I set a default role for new invites?**
Yes, on the Business and Enterprise plans. Go to **Settings → Members →
Defaults**.

**How do I invite someone with SSO enabled?**
If SSO is enabled, you can either invite specific emails as usual or enable
"just-in-time provisioning" in SSO settings so users are created
automatically on first login.
