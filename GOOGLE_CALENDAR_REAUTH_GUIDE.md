# Google Calendar Re-authentication Guide

Your Google Calendar syncs are currently failing because the authentication token has expired. Follow these steps to re-authenticate.

---

## Quick Start (Easiest Method)

### Step 1: Open Terminal
- Open the Terminal app on your Mac
- Or use the existing terminal window

### Step 2: Run the Re-authentication Script
```bash
cd /Users/comstudio/Scripts/StudioProcesses
./reauth_google_calendar.sh
```

### Step 3: Follow the On-Screen Instructions
The script will:
1. Remove the old expired token
2. Activate the virtual environment
3. Launch your browser for authentication

---

## What You'll See During Authentication

### Browser Window Opens
- You'll see a Google sign-in page
- **Important**: You may see a warning that says "This app isn't verified"

### If You See the Warning Screen:
1. Click **"Advanced"** (at the bottom left)
2. Click **"Go to [Your App Name] (unsafe)"**
   - This is safe - it's your own app
   - Google shows this for apps in testing mode

### Grant Permissions:
1. Select your Google account
2. Review the permissions requested:
   - See, edit, share, and permanently delete calendars
3. Click **"Allow"**

### Success!
- The browser will show "The authentication flow has completed"
- You can close the browser window
- Return to Terminal

---

## Manual Method (If Script Doesn't Work)

If you prefer to do it manually or the script has issues:

### Step 1: Open Terminal
```bash
cd /Users/comstudio/Scripts/StudioProcesses
```

### Step 2: Remove Old Token
```bash
rm token.pickle
```

### Step 3: Activate Virtual Environment
```bash
source venv/bin/activate
```

### Step 4: Run Authentication
```bash
python3 film_date_calendar_sync.py
```

### Step 5: Complete Browser Authentication
Follow the browser instructions (same as above)

---

## Verification

After authentication completes, verify it worked:

### Check Token File Exists:
```bash
ls -l token.pickle
```
You should see a file with today's date.

### Check Recent Logs (wait 30 minutes for next cron run):
```bash
tail -20 film_calendar_sync.log
tail -20 wov_sync.log
```
You should see successful sync messages instead of errors.

---

## Troubleshooting

### "No module named 'google'" Error
Your virtual environment isn't activated. Run:
```bash
source venv/bin/activate
```

### "credentials.json not found" Error
The credentials file is missing. You need to:
1. Go to Google Cloud Console
2. Download new OAuth 2.0 credentials
3. Save as `credentials.json` in `/Users/comstudio/Scripts/StudioProcesses/`

### Browser Doesn't Open
The authentication URL will be printed in the terminal. Copy and paste it into your browser manually.

### Still Getting Errors After Re-auth
1. Check that credentials.json is valid
2. Verify Google Calendar API is enabled in Google Cloud Console
3. Check OAuth consent screen is configured
4. Ensure you're using the correct Google account

---

## What Gets Fixed

Once re-authentication is complete, these cron jobs will resume working:

✅ **Film Date Calendar Sync** (every 30 minutes)
- Syncs Asana film dates to Google Calendar

✅ **Due Date Calendar Sync** (every 30 minutes)
- Syncs Asana due dates to Google Calendar

✅ **WOV Calendar Sync** (every 30 minutes)
- Syncs WOV events to Google Calendar

---

## Need Help?

If you encounter issues:
1. Check the error messages in Terminal
2. Look at the log files: `film_calendar_sync.log`, `wov_sync.log`
3. Verify your Google Cloud Console settings
4. Make sure the OAuth app is set to "Testing" or "Published" status
