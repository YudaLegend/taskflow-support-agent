# Troubleshooting: Sync Problems

This guide covers issues where TaskFlow data doesn't appear to update
correctly across devices, browsers, or team members.

## Symptom: Changes I made on mobile don't appear on the web

**Possible causes:**

- Your mobile device is offline or was offline when you made the change
- The mobile app's background sync was paused by the OS
- There's a temporary connection issue between the app and TaskFlow servers

**How to fix:**

1. Open the TaskFlow mobile app and check the top of the screen for an
   "Offline" indicator. If it's there, connect to Wi-Fi or mobile data.
2. Pull down on any screen to trigger a manual refresh.
3. If changes still don't sync after 1 minute, force-close the app and
   reopen it.
4. As a last resort, sign out and back in on the mobile app.

## Symptom: Tasks I created are missing after refresh

**Possible causes:**

- The task was created in a filtered view and the filter hides it
- The task was created in a different project than you thought
- A teammate deleted or moved the task

**How to fix:**

1. Clear all filters: click the **Clear filters** button at the top of the
   project view.
2. Use the global search bar (press `/`) to search for the task by title.
3. Check the **Activity log** at the project level (**··· → Activity**) to
   see recent changes and who made them.

## Symptom: Different teammates see different data

**Possible causes:**

- One of you has a filtered view applied and doesn't realize it
- One of you is a Guest and can't see certain tasks
- One of you has stale data cached in the browser

**How to fix:**

1. Compare filters at the top of the view — they're personal per user
2. Check each user's role: Guests (Business+) may have restricted
   visibility
3. Have each user do a hard refresh of the browser (Ctrl+Shift+R on
   Windows/Linux, Cmd+Shift+R on Mac) to clear the cache

## Symptom: Comments posted by my teammates don't appear

**Possible causes:**

- Your browser tab is stale (TaskFlow uses WebSockets to push updates, but
  some networks block them)
- A browser extension is interfering with WebSockets
- The team member posted to a different task than you think

**How to fix:**

1. Refresh the browser. New comments should appear immediately after a
   reload.
2. Try an incognito window to rule out extensions.
3. If your network blocks WebSockets (common on some corporate networks),
   TaskFlow falls back to polling every 30 seconds. This is slower but
   should still work. Ask your IT team to allow WebSocket traffic to
   `*.taskflow.example.com` for a better experience.

## Symptom: Integration data (Slack, Google Drive, GitHub) is out of sync

**Possible causes:**

- The third-party service had an outage
- Your integration credentials expired
- A rate limit was hit

**How to fix:**

1. Check status.taskflow.example.com for known outages.
2. Go to **Settings → Integrations** and look for a warning badge next to
   the affected integration. If you see one, click it to re-authorize.
3. For Google Drive specifically: if you changed your Google password
   recently, you'll need to reconnect.

## Symptom: "Conflict detected" when saving a task

**Possible causes:**

- Two people edited the same task at the same time
- You edited a task that was already being edited offline on another device

**How to fix:**

1. TaskFlow shows both versions side by side. Review them and pick which
   fields to keep.
2. Click **Save** on your merged version to resolve the conflict.
3. To reduce conflicts, avoid editing the same task simultaneously from
   multiple devices.

## Symptom: Mobile offline changes were lost after reconnecting

**Possible causes:**

- The conflict resolution rule (most recent change wins) discarded your
  offline change in favor of a more recent online change
- The app was uninstalled before syncing

**How to fix:**

1. This is expected behavior, not a bug — TaskFlow prioritizes the most
   recent change across all devices to keep data consistent.
2. To avoid losing offline work in the future: connect to the internet and
   let the app sync before editing the same task on another device.

## Still having sync issues?

Email support@taskflow.example.com with:

- What device and browser you're using
- A screenshot showing the issue
- The approximate time you noticed the problem (we use this to check logs)
- Your workspace name

## Related

- Mobile apps — offline mode details
- General FAQ — data storage and backups
