#!/bin/bash
# Interactive Email Setup for Capacity Alerts

echo "======================================================================"
echo "Gmail App Password Setup for Capacity Alerts"
echo "======================================================================"
echo ""
echo "📧 Emails will be sent to: zwelliver@perimeter.org"
echo ""
echo "First, you need to create a Gmail App Password:"
echo ""
echo "1. Open this link in your browser:"
echo "   https://myaccount.google.com/apppasswords"
echo ""
echo "2. Sign in if needed"
echo ""
echo "3. Create app password:"
echo "   - App: Mail (or Other > 'Capacity Alerts')"
echo "   - Device: Other > 'Mac Video Production'"
echo ""
echo "4. Click GENERATE"
echo ""
echo "5. Copy the 16-character password shown"
echo "   (looks like: abcd efgh ijkl mnop)"
echo ""
echo "======================================================================"
echo ""
read -p "Press Enter when you have your app password ready..."
echo ""
echo "======================================================================"
echo "Email Configuration"
echo "======================================================================"
echo ""

# Get Gmail address
read -p "Enter your Gmail address (e.g., your.email@gmail.com): " GMAIL_ADDRESS

# Get app password
echo ""
echo "Enter the 16-character app password (spaces are OK):"
read -s APP_PASSWORD

# Remove spaces from password
APP_PASSWORD=$(echo "$APP_PASSWORD" | tr -d ' ')

echo ""
echo ""
echo "Testing email configuration..."
echo ""

# Update .env file
ENV_FILE="$HOME/Scripts/StudioProcesses/.env"

# Backup existing .env
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"

# Remove old email config if exists
sed -i.tmp '/^SMTP_SERVER=/d' "$ENV_FILE"
sed -i.tmp '/^SMTP_PORT=/d' "$ENV_FILE"
sed -i.tmp '/^SMTP_USER=/d' "$ENV_FILE"
sed -i.tmp '/^SMTP_PASSWORD=/d' "$ENV_FILE"
rm -f "$ENV_FILE.tmp"

# Add new email config
cat >> "$ENV_FILE" << EOF

# Email Configuration (added $(date +%Y-%m-%d))
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=$GMAIL_ADDRESS
SMTP_PASSWORD=$APP_PASSWORD
EOF

echo "✅ Configuration saved to .env"
echo ""
echo "======================================================================"
echo "Testing Email Setup"
echo "======================================================================"
echo ""

# Test the email
cd "$HOME/Scripts/StudioProcesses"
source venv/bin/activate

echo "Sending test email to zwelliver@perimeter.org..."
echo ""

python3 << 'PYEOF'
import os
import sys
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv(".env")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT = "zwelliver@perimeter.org"

try:
    print(f"📧 Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    print(f"🔐 Logging in as {SMTP_USER}...")
    server.login(SMTP_USER, SMTP_PASSWORD)

    print(f"✉️  Sending test email to {RECIPIENT}...")

    msg = MIMEText("This is a test email from the Capacity Alert System.\n\nIf you're seeing this, email alerts are working correctly!\n\n✅ Setup Complete")
    msg['Subject'] = "✅ Capacity Alert System - Test Email"
    msg['From'] = SMTP_USER
    msg['To'] = RECIPIENT

    server.send_message(msg)
    server.quit()

    print("")
    print("✅ SUCCESS! Test email sent successfully!")
    print(f"   Check zwelliver@perimeter.org inbox")
    print("")
    sys.exit(0)

except Exception as e:
    print("")
    print(f"❌ ERROR: {e}")
    print("")
    print("Common issues:")
    print("  - Wrong app password (must be 16 characters)")
    print("  - 2-Step Verification not enabled")
    print("  - Gmail security blocking the login")
    print("")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo "======================================================================"
    echo "🎉 Email Setup Complete!"
    echo "======================================================================"
    echo ""
    echo "✅ Configuration saved"
    echo "✅ Test email sent"
    echo ""
    echo "Next Steps:"
    echo "  1. Check zwelliver@perimeter.org for test email"
    echo "  2. Weekly reports will be sent every Monday at 8am"
    echo "  3. Over-capacity alerts will be sent automatically"
    echo ""
    echo "Test anytime with:"
    echo "  python ~/Scripts/StudioProcesses/weekly_capacity_report.py"
    echo ""
else
    echo "======================================================================"
    echo "❌ Setup Failed"
    echo "======================================================================"
    echo ""
    echo "Please check the error above and try again."
    echo ""
    echo "To retry: bash ~/Scripts/StudioProcesses/setup_email.sh"
    echo ""
    echo "Your .env has been backed up to: $ENV_FILE.backup.*"
    echo ""
fi
