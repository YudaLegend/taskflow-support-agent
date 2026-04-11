# Troubleshooting: Login Issues

This guide covers the most common reasons users can't log into TaskFlow and
how to fix them.

## Symptom: "Invalid email or password"

**Possible causes:**

- The password is wrong
- You're using the wrong email address (many users have multiple)
- Caps Lock is on

**How to fix:**

1. Double-check your email address. If you have multiple, try each.
2. Make sure Caps Lock is off.
3. If you still can't get in, click **Forgot password?** on the login page
   to receive a reset link. The link is valid for 1 hour.
4. Check your spam folder if the reset email doesn't arrive within 2
   minutes.

## Symptom: "Account not found"

**Possible causes:**

- You never created an account with this email
- Your account was deleted
- You're trying to log into the wrong region (EU vs US)

**How to fix:**

1. Confirm which email you used to sign up.
2. If you think your account existed but no longer works, email
   support@taskflow.example.com with the email address in question and
   we'll investigate.
3. If you use an Enterprise workspace with US data residency, make sure
   you're signing in at the correct URL (your workspace admin can confirm).

## Symptom: "Your account is locked"

**Possible causes:**

- Too many failed login attempts in a short period
- Suspicious activity detected (for example, logins from many countries)

**How to fix:**

1. Wait 15 minutes and try again — most lockouts clear automatically.
2. If the lock persists, use **Forgot password?** to reset. A successful
   reset unlocks the account.
3. If you see a message saying "Contact support," email
   support@taskflow.example.com with your email and a description of what
   happened.

## Symptom: Two-factor code isn't working

**Possible causes:**

- Your device clock is out of sync (TOTP codes are time-based)
- You're entering a code that already expired (codes are valid for 30
  seconds each)
- You reset the authenticator app or switched devices

**How to fix:**

1. Check that your device's time is set to automatic. On iOS:
   **Settings → General → Date & Time → Set Automatically**. On Android:
   **Settings → System → Date & Time → Automatic**.
2. Wait for the next code (up to 30 seconds) and try again.
3. If you've lost your authenticator, use one of the **recovery codes** you
   saved when you enabled 2FA.
4. If you've lost both the authenticator and your recovery codes, email
   support@taskflow.example.com. Account recovery takes up to 5 business
   days and requires identity verification.

## Symptom: SSO login fails

**Possible causes:**

- Your IT admin hasn't enabled TaskFlow in the SSO provider yet
- You're using the wrong SSO login URL
- Your SSO session has expired

**How to fix:**

1. Check with your IT administrator that TaskFlow is listed as an approved
   app in your SSO provider.
2. Use the SSO login URL provided by your admin, not the regular TaskFlow
   login page.
3. If SSO keeps looping, clear your browser cookies for
   taskflow.example.com and try again.

## Symptom: "Session expired" immediately after login

**Possible causes:**

- Browser cookies are blocked or cleared automatically
- A browser extension is interfering (ad blockers, privacy tools)
- You're using a very old browser version

**How to fix:**

1. Make sure cookies are enabled for taskflow.example.com.
2. Try an incognito/private window to rule out extensions.
3. Update your browser to the latest version. TaskFlow supports current
   versions of Chrome, Firefox, Safari, and Edge.

## Symptom: Can't log in on mobile

**Possible causes:**

- You're using an outdated version of the app
- Your device's OS is too old
- Your account has 2FA and you're entering the wrong code format

**How to fix:**

1. Update the TaskFlow app to the latest version from the App Store or
   Google Play.
2. Make sure your iOS is 15+ or your Android is 9 (Pie)+.
3. If 2FA is enabled, enter the 6-digit code from your authenticator app,
   not your password.

## Still can't log in?

Email support@taskflow.example.com with:

- The email address you're trying to use
- The exact error message (screenshot if possible)
- What you've already tried from this guide

Support will respond within the time window defined by your plan.

## Related

- Account management — changing your password, enabling 2FA
- General FAQ — account and workspace basics
