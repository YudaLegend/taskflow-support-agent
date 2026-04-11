# Troubleshooting: Notifications

This guide covers common problems with notifications in TaskFlow — missing
ones, duplicated ones, and configuration issues.

## Symptom: I'm not receiving email notifications

**Possible causes:**

- Your email notification preferences are disabled
- Emails are landing in spam
- Your email provider is blocking TaskFlow
- Your email address is unverified

**How to fix:**

1. Go to **Settings → Notifications → Email** and make sure at least some
   notification types are enabled.
2. Check the spam folder of your email inbox. If you find TaskFlow emails
   there, mark them as "Not spam".
3. Add `support@taskflow.example.com` and `notifications@taskflow.example.com`
   to your email contacts or allowlist.
4. Check **Settings → Account → Email** — if your email shows
   "Unverified", click **Resend verification** and follow the link.
5. If you use Gmail and emails still don't arrive, ensure TaskFlow messages
   aren't filtered into the "Promotions" or "Updates" tab.

## Symptom: I'm not receiving push notifications on mobile

**Possible causes:**

- Push notifications are disabled at the OS level
- Push notifications are disabled in the TaskFlow app
- Background app refresh is off
- You're on iOS Focus mode or Android Do Not Disturb

**How to fix:**

1. **iOS:** Go to **Settings → Notifications → TaskFlow** and enable
   **Allow Notifications**.
2. **Android:** Go to **Settings → Apps → TaskFlow → Notifications** and
   enable them.
3. In the TaskFlow mobile app, go to **Settings → Notifications → Mobile**
   and make sure notifications for the events you care about are enabled.
4. Check if Focus mode (iOS) or Do Not Disturb (Android) is active — these
   silence notifications until turned off.
5. On iOS: enable **Background App Refresh** for TaskFlow in
   **Settings → General → Background App Refresh**.

## Symptom: I'm getting too many notifications

**Possible causes:**

- You're a member of many projects
- You're watching tasks you don't need to follow
- `@everyone` or `@project` mentions are triggering for every task

**How to fix:**

1. Go to **Settings → Notifications** and disable notification types you
   don't need. For example, if you don't care about every comment on tasks
   you're just watching, disable "Comments on watched tasks".
2. Unwatch tasks you don't need updates for — open a task and click the
   **eye** icon to toggle watching.
3. Mute specific projects from **Project → ··· → Mute notifications**.
   Muted projects still appear in your sidebar but don't generate
   notifications.
4. If your team uses `@everyone` too often, ask them to use more targeted
   mentions.

## Symptom: I'm getting duplicate notifications

**Possible causes:**

- You have the same account signed in on multiple devices with push
  enabled on each
- You're subscribed to both email and push for the same events
- An integration (Slack, email) is echoing events already shown in-app

**How to fix:**

1. Go to **Settings → Notifications** and pick a primary channel for each
   event type. For example, "mentions" go to push, "status changes" go to
   email, but not both.
2. On mobile, you can disable push while keeping email active (or vice
   versa) from the same settings page.
3. Review connected integrations (**Settings → Integrations**) and turn off
   notifications from any that are redundant.

## Symptom: Notifications are delayed

**Possible causes:**

- Mobile OS is throttling background activity to save battery
- Push notification servers are experiencing latency
- Your network is slow

**How to fix:**

1. On iOS, disable **Low Power Mode** temporarily to see if that's the
   cause.
2. On Android, remove TaskFlow from any battery optimization list
   (**Settings → Battery → Battery optimization → TaskFlow → Don't
   optimize**).
3. Check status.taskflow.example.com for any reported push notification
   latency.
4. Connect to a faster network if you're on spotty mobile data.

## Symptom: I'm getting notifications for someone else's account

**Possible causes:**

- You signed up with an email alias someone else also uses
- A previous user of your device left their account signed in
- Your email address was typed incorrectly when someone invited you

**How to fix:**

1. Make sure you're signed into the correct TaskFlow account — check
   **Settings → Account** for the email address shown.
2. If you see someone else's email address, sign out and sign into your
   own account.
3. If the wrong emails keep coming, email support@taskflow.example.com so
   we can investigate.

## Notification preference reference

Go to **Settings → Notifications** to configure:

- **@mentions** — when someone mentions you in a comment
- **Task assigned to me** — when you're assigned a new task
- **Due date reminders** — 1 hour and 1 day before a task is due
- **Watched tasks** — changes on tasks you've explicitly chosen to watch
- **Project changes** — status changes, new tasks in projects you're a
  member of
- **Workspace events** — admin announcements, billing notices

Each type can be independently configured for email, push (mobile), and
in-app notification channels.

## Still having notification issues?

Email support@taskflow.example.com with:

- Which type of notification is affected
- Which channel (email, push, in-app)
- Your device and OS version
- A rough timeline of when it started

## Related

- Account management — verifying email addresses
- Mobile apps — push notification setup
