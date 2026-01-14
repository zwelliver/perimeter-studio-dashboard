#!/bin/bash
# Alternative Email Setup - Use a dedicated Gmail account

echo "======================================================================"
echo "Alternative Email Setup for Capacity Alerts"
echo "======================================================================"
echo ""
echo "If you're having trouble with app passwords, you can:"
echo ""
echo "Option 1: Create a new Gmail account for alerts"
echo "=========================================="
echo ""
echo "1. Go to: https://accounts.google.com/signup"
echo "2. Create new account (e.g., perimeter-alerts@gmail.com)"
echo "3. Complete setup"
echo "4. Enable 2-Step Verification on the NEW account"
echo "5. Create app password on the NEW account"
echo ""
echo "Benefits:"
echo "  ✅ Dedicated account for automated emails"
echo "  ✅ Won't affect your personal account"
echo "  ✅ Easier to manage permissions"
echo ""
echo "----------------------------------------------------------------------"
echo ""
echo "Option 2: Use Gmail with 'Less secure apps' (Not recommended)"
echo "=========================================="
echo ""
echo "⚠️  Not recommended for security reasons"
echo ""
echo "----------------------------------------------------------------------"
echo ""
echo "Option 3: Use Microsoft 365 / Perimeter Email"
echo "=========================================="
echo ""
echo "If Perimeter has an email server, we can use that instead."
echo ""
echo "You would need:"
echo "  - SMTP server address (e.g., smtp.perimeter.org)"
echo "  - Port (usually 587)"
echo "  - Your perimeter email credentials"
echo ""
echo "======================================================================"
echo ""

read -p "Which option would you like to try? (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "Great! Follow these steps:"
        echo ""
        echo "1. Create Gmail account: https://accounts.google.com/signup"
        echo "   Suggested name: perimeter-video-alerts@gmail.com"
        echo ""
        echo "2. Enable 2-Step Verification:"
        echo "   https://myaccount.google.com/security"
        echo ""
        echo "3. Create App Password:"
        echo "   https://myaccount.google.com/apppasswords"
        echo ""
        echo "4. Then run: bash ~/Scripts/StudioProcesses/setup_email.sh"
        echo ""
        ;;
    3)
        echo ""
        echo "Let's set up with Perimeter email server:"
        echo ""
        read -p "SMTP Server (e.g., smtp.perimeter.org): " SMTP_SERVER
        read -p "SMTP Port (usually 587 or 465): " SMTP_PORT
        read -p "Your email address: " EMAIL_USER
        echo "Enter your email password:"
        read -s EMAIL_PASS

        ENV_FILE="$HOME/Scripts/StudioProcesses/.env"
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"

        sed -i.tmp '/^SMTP_SERVER=/d' "$ENV_FILE"
        sed -i.tmp '/^SMTP_PORT=/d' "$ENV_FILE"
        sed -i.tmp '/^SMTP_USER=/d' "$ENV_FILE"
        sed -i.tmp '/^SMTP_PASSWORD=/d' "$ENV_FILE"
        rm -f "$ENV_FILE.tmp"

        cat >> "$ENV_FILE" << EOF

# Email Configuration (Microsoft/Perimeter)
SMTP_SERVER=$SMTP_SERVER
SMTP_PORT=$SMTP_PORT
SMTP_USER=$EMAIL_USER
SMTP_PASSWORD=$EMAIL_PASS
EOF

        echo ""
        echo "✅ Configuration saved!"
        echo ""
        echo "Testing..."
        cd "$HOME/Scripts/StudioProcesses"
        source venv/bin/activate
        python weekly_capacity_report.py
        ;;
    *)
        echo ""
        echo "Invalid choice. Please run again and select 1, 2, or 3."
        ;;
esac
