# Account Management

Your TaskFlow account is tied to a single email address. All your account
settings live under **Settings → Account** in the web app.

## Changing your email address

1. Go to **Settings → Account → Email**
2. Enter the new email address
3. Check the new inbox for a verification link
4. Click the link within 24 hours to confirm

Your old email remains active until the new one is verified, so you won't
lose access if you make a typo.

## Changing your password

1. Go to **Settings → Account → Password**
2. Enter your current password
3. Enter and confirm your new password
4. Click **Update password**

Passwords must be at least 10 characters long and include at least one
number or symbol. You'll be signed out of all other sessions after changing
your password.

## Forgot your password

If you've forgotten your password, use the **Forgot password?** link on the
login page. We'll email you a reset link that's valid for 1 hour.

If you don't receive the email within a few minutes:

- Check your spam folder
- Verify you're using the correct email address
- Make sure support@taskflow.example.com is not blocked by your provider

## Enabling two-factor authentication (2FA)

Two-factor authentication adds a second verification step when you log in.

1. Go to **Settings → Account → Security**
2. Click **Enable two-factor authentication**
3. Scan the QR code with an authenticator app (Google Authenticator, Authy,
   1Password, etc.)
4. Enter the 6-digit code from your app to confirm
5. **Save your recovery codes** in a safe place — you'll need them if you
   lose access to your authenticator

TaskFlow supports TOTP-based 2FA. SMS-based 2FA is not supported for
security reasons.

## Recovery codes

When you enable 2FA, you receive 10 single-use recovery codes. Each code
can be used once to log in if you lose your authenticator. You can generate
new codes at any time from **Settings → Account → Security**, which
invalidates the old ones.

## Managing connected sessions

You can see all devices currently logged into your account at
**Settings → Account → Active sessions**. Click **Sign out** next to any
session to revoke it immediately.

If you see a session you don't recognize, sign it out and change your
password right away.

## Deleting your account

Deleting your account is permanent and cannot be undone.

1. Go to **Settings → Account → Delete account**
2. Type your email address to confirm
3. Click **Delete my account**

**What happens when you delete your account:**

- Your personal profile is removed immediately
- Tasks you created remain in their projects but are reassigned to "Deleted
  user"
- Comments you wrote stay visible for context but show "Deleted user"
- If you're the only admin of a workspace, you must transfer ownership or
  delete the workspace first
- Billing is prorated and any remaining balance is refunded within 10
  business days

**Data retention:** we retain anonymized logs for 30 days after account
deletion for security auditing, then permanently delete them.

## Frequently asked questions

**Can I merge two TaskFlow accounts?**
No. If you accidentally created two accounts, contact support and we can
help you transfer your work from one to the other, but the accounts
themselves can't be merged.

**What if I lose access to my email and my 2FA?**
Contact support@taskflow.example.com from any email address. We'll ask you
to verify account ownership through other means (invoice details, workspace
admins vouching for you, etc.). Recovery can take up to 5 business days.

**Is my profile visible to people outside my workspace?**
No. Your profile is only visible to members of workspaces you belong to.

**Can I use the same email for multiple workspaces?**
Yes. A single TaskFlow account can be a member of unlimited workspaces.
