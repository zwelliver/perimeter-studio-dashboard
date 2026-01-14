# Gmail App Password Setup Instructions

## Step 1: Enable 2-Step Verification (if not already enabled)

1. Go to: https://myaccount.google.com/security
2. Look for "2-Step Verification" section
3. If it says "Off", click to turn it ON
4. Follow the prompts to set up (usually phone number verification)

## Step 2: Generate App Password

1. **Go to App Passwords page:**
   https://myaccount.google.com/apppasswords

2. **Sign in** with your Google account (if prompted)

3. **Select app:** Choose "Mail" or "Other (Custom name)"
   - If "Other", enter: "Capacity Alert System"

4. **Select device:** Choose "Other (Custom name)"
   - Enter: "Mac Video Production"

5. **Click "Generate"**

6. **Copy the 16-character password** (looks like: "abcd efgh ijkl mnop")
   - ⚠️ You'll only see this once!
   - Write it down or copy it immediately

## Step 3: Add to .env File

The password will be 16 characters with spaces. You can enter it with or without spaces.

Example: `abcdefghijklmnop` or `abcd efgh ijkl mnop`

## Troubleshooting

**If you don't see "App passwords" option:**
- Make sure 2-Step Verification is enabled first
- Wait a few minutes after enabling 2-Step Verification
- Try this direct link: https://myaccount.google.com/apppasswords
- If still not available, your Google Workspace admin may have disabled it

**Alternative: Use a dedicated Gmail account**
- Create a new Gmail account specifically for sending alerts
- Enable 2-Step Verification on that account
- Generate app password for that account
- Use that email for SMTP_USER

## Security Notes

✅ App passwords are safer than using your main password
✅ They can be revoked at any time
✅ They only work for the specific app/device
✅ Your main password remains secure
