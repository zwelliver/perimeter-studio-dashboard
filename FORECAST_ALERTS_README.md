# Forecast Pipeline Alert System

Automated email alerts for forecasted projects that haven't been moved to the production pipeline when they're within 30 days of their due date.

## How It Works

The system:
1. Fetches all incomplete tasks from the "Forecast" Asana project
2. Checks if each forecasted project exists in Preproduction, Production, or Post Production
3. Identifies projects that are within 30 days of their due date but NOT in the pipeline
4. Sends an email alert with the list of projects requiring attention

## Configuration

### Required Environment Variables (.env)

Add these to your `.env` file:

```bash
# Email Configuration for Forecast Alerts
ALERT_EMAIL_FROM=studio@perimeter.org
ALERT_EMAIL_TO=your.email@perimeter.org
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### Gmail Setup

If using Gmail:
1. Go to your Google Account settings
2. Navigate to Security > 2-Step Verification > App passwords
3. Generate an app-specific password for "Mail"
4. Use that password for `SMTP_PASSWORD`

**Note:** Never use your actual Gmail password - always use an app-specific password.

### Alternative Email Providers

For other email providers, update:
- `SMTP_SERVER`: Your provider's SMTP server (e.g., smtp.office365.com for Outlook)
- `SMTP_PORT`: Usually 587 for TLS or 465 for SSL
- `SMTP_USERNAME`: Your email address
- `SMTP_PASSWORD`: Your email password or app-specific password

## Schedule

The automation runs **daily at 9:00 AM** via macOS launchd.

Configuration file: `~/Library/LaunchAgents/com.perimeter.forecast-checker.plist`

## Manual Testing

Run the script manually to test:

```bash
cd /Users/comstudio/Scripts/StudioProcesses
source venv/bin/activate
python3 check_forecast_pipeline.py
```

## Logs

Check the logs to see when the script last ran:

```bash
# View standard output log
cat /Users/comstudio/Scripts/StudioProcesses/logs/forecast_checker.log

# View error log
cat /Users/comstudio/Scripts/StudioProcesses/logs/forecast_checker_error.log
```

## Managing the Automation

### Check Status
```bash
launchctl list | grep perimeter.forecast
```

### Unload (Disable)
```bash
launchctl unload ~/Library/LaunchAgents/com.perimeter.forecast-checker.plist
```

### Reload (Enable)
```bash
launchctl load ~/Library/LaunchAgents/com.perimeter.forecast-checker.plist
```

### Change Schedule

Edit the plist file and change the `StartCalendarInterval`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>      <!-- Change hour (0-23) -->
    <key>Minute</key>
    <integer>0</integer>       <!-- Change minute (0-59) -->
</dict>
```

After editing, unload and reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.perimeter.forecast-checker.plist
launchctl load ~/Library/LaunchAgents/com.perimeter.forecast-checker.plist
```

## Email Content

When alerts are found, you'll receive an email with:
- Project name
- Due date
- Days until due
- Urgency indicator (color-coded)
- Direct link to view in Asana

Example alert:
- ⚠️ Projects due within 7 days (RED - urgent)
- Projects due within 14 days (YELLOW - warning)
- Projects due within 30 days (BLUE - normal)

## Troubleshooting

### No Emails Received

1. Check email configuration in `.env`
2. Verify SMTP credentials are correct
3. Check error log: `cat logs/forecast_checker_error.log`
4. Test manually: `python3 check_forecast_pipeline.py`

### Script Not Running

1. Check if agent is loaded: `launchctl list | grep perimeter.forecast`
2. Check for errors: `cat logs/forecast_checker_error.log`
3. Verify file paths in the plist file match your system

### False Positives

If you're getting alerts for projects already in the pipeline, it may be a name mismatch:
- Ensure project names are identical between Forecast and pipeline
- The script normalizes names (removes checkboxes, whitespace) automatically
- Case-insensitive matching is used

## Support

For issues or questions, contact the Perimeter Studio team.
