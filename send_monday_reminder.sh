#!/bin/bash
# Send reminder via Slack webhook or direct message

MESSAGE="📅 Monday Reminder:\n- Figure out DD set\n- Work on frontier video"

# Option 1: Using Slack webhook (if you have one configured)
# curl -X POST YOUR_SLACK_WEBHOOK_URL -H 'Content-Type: application/json' -d "{\"text\":\"$MESSAGE\"}"

# Option 2: Using clawdbot API (if gateway is running)
# curl -X POST http://localhost:18789/api/chat -H 'Content-Type: application/json' -d "{\"message\":\"$MESSAGE\",\"channel\":\"studio-production-pipeline\"}"

echo "Reminder: Figure out DD set and work on frontier video"
