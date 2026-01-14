#!/bin/bash
# Google Calendar Re-authentication Script
# This script helps you re-authenticate with Google Calendar API

echo "=========================================="
echo "Google Calendar Re-authentication"
echo "=========================================="
echo ""

# Change to script directory
cd /Users/comstudio/Scripts/StudioProcesses

# Step 1: Remove old token
echo "Step 1: Removing expired token..."
if [ -f "token.pickle" ]; then
    rm token.pickle
    echo "✅ Old token removed"
else
    echo "ℹ️  No old token found (this is fine)"
fi
echo ""

# Step 2: Activate virtual environment
echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Step 3: Run authentication
echo "Step 3: Starting authentication process..."
echo ""
echo "📋 Instructions:"
echo "   1. A browser window will open"
echo "   2. Sign in with your Google account"
echo "   3. Click 'Allow' to grant calendar access"
echo "   4. You may see a warning - click 'Advanced' then 'Go to [app name] (unsafe)'"
echo "   5. Click 'Allow' on the permissions screen"
echo ""
echo "Press ENTER to continue..."
read

echo "🔐 Launching authentication..."
python3 film_date_calendar_sync.py

# Check if successful
if [ -f "token.pickle" ]; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Authentication complete"
    echo "=========================================="
    echo ""
    echo "Your calendar syncs should now work:"
    echo "  • Film Date Calendar Sync"
    echo "  • Due Date Calendar Sync"
    echo "  • WOV Calendar Sync"
    echo ""
    echo "These will run automatically via cron."
else
    echo ""
    echo "=========================================="
    echo "❌ Authentication failed"
    echo "=========================================="
    echo ""
    echo "Please check the error messages above."
    echo "You may need to:"
    echo "  1. Check your credentials.json file"
    echo "  2. Verify OAuth consent screen settings"
    echo "  3. Check if the API is enabled in Google Cloud Console"
fi
