# Team Capacity Tracking Guide

## 📊 View Current Capacity

### Option 1: Interactive Dashboard (Recommended)
```bash
cd ~/Scripts/StudioProcesses
source venv/bin/activate
python capacity_dashboard.py
```

**Output:**
```
======================================================================
TEAM CAPACITY DASHBOARD - 2025-11-17 15:11
======================================================================

📊 CAPACITY SUMMARY
----------------------------------------------------------------------
Team Member          Usage           Limit      Status
----------------------------------------------------------------------
Zach Welliver         35.0% /  50%  ( 70.0%)  📈 High
Nick Clark            22.5% / 100%  ( 22.5%)  ✅ OK
Adriel Abella        110.0% / 100%  (110.0%)  🚨 OVER LIMIT
----------------------------------------------------------------------

📋 DETAILED TASK BREAKDOWN
======================================================================

Zach Welliver (35.0%):
  •  15.5% - Christmas Campaign (Preproduction)
  •  12.0% - Website Redesign (Preproduction)
  •   7.5% - Social Media Series (Preproduction)

Nick Clark (22.5%):
  •  15.0% - Interview Video (Production)
  •   7.5% - Event Highlight (Production)

Adriel Abella (110.0%):
  •  30.0% - Major Edit Project (Post Production)
  •  25.0% - Conference Recap (Post Production)
  ...
```

### Option 2: Check Log Files
```bash
# Latest capacity report
tail -20 ~/Scripts/StudioProcesses/video_scorer.log

# Timeline script report
tail -20 ~/Scripts/StudioProcesses/timeline.log

# Over-capacity alerts only
grep "CAPACITY" ~/Scripts/StudioProcesses/manipulation_audit.log
```

### Option 3: View in Asana
Every task has a **"Percent allocation"** custom field showing its weekly capacity cost.

---

## 🚨 Capacity Alerts

### Current Alert System (File-based)

When someone goes over capacity, alerts are automatically logged to:
```bash
~/Scripts/StudioProcesses/capacity_alerts.txt
```

**View alerts:**
```bash
cat ~/Scripts/StudioProcesses/capacity_alerts.txt
```

**Example alert:**
```
======================================================================
CAPACITY ALERT - 2025-11-17 15:30:00
======================================================================
Team Member: Zach Welliver
Current Usage: 55.0%
Limit: 50%
Over by: 5.0%

Active Tasks:
    • 15.5% - Christmas Campaign
    • 12.0% - Website Redesign
    • 7.5% - Social Media Series
======================================================================
```

---

## 🔔 Enable Email/Slack Alerts (Optional)

### Email Alerts

1. **Add to `.env` file:**
```bash
# Email configuration
ALERT_EMAIL=your-email@perimeter.org
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

2. **Enable in video_scorer.py** (line 691):
```python
# Uncomment this line:
send_email_alert(team_member, new_total, capacity_limit, alert_tasks)
```

### Slack Alerts

1. **Create Slack Webhook:**
   - Go to: https://api.slack.com/messaging/webhooks
   - Create incoming webhook for your channel
   - Copy webhook URL

2. **Add to `.env` file:**
```bash
SLACK_WEBHOOK_CAPACITY=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. **Enable in video_scorer.py** (line 692):
```python
# Uncomment this line:
send_slack_alert(team_member, new_total, capacity_limit, alert_tasks)
```

---

## 📅 When Alerts Trigger

Alerts are sent when:
- A new task assignment would put someone **over their capacity limit**
- Runs automatically every **15 minutes** via cron

**Capacity Limits:**
- Zach Welliver: 50%
- Nick Clark: 100%
- Adriel Abella: 100%

---

## 🔍 How Capacity is Calculated

**Formula (Option 3 - Weighted):**
```
Base = Complexity × 10%
Priority Multiplier = Priority Score / 8
Weekly Allocation = (Base × Priority Multiplier) / Duration in weeks
```

**Example:**
- Priority: 8, Complexity: 3, Duration: 4 weeks
- Base: 3 × 10 = 30%
- Multiplier: 8 / 8 = 1.0
- **Allocation: (30 × 1.0) / 4 = 7.5% per week**

---

## 🔄 Workflow Integration

### Automatic Assignment & Tracking:

1. **Task enters Preproduction** (form submitted)
   - ✅ Grok AI scores it
   - ✅ Calculates weekly allocation %
   - ✅ Assigns to **Zach Welliver**
   - ✅ Checks if Zach over 50%
   - ✅ Alerts if needed

2. **Zach approves → moves to Production**
   - ✅ Reassigns to **Nick Clark**
   - ✅ Capacity transfers from Zach to Nick
   - ✅ Generates production timeline

3. **Nick completes → moves to Post Production**
   - ✅ Reassigns to **Adriel Abella**
   - ✅ Capacity transfers from Nick to Adriel

---

## 📝 Quick Commands

```bash
# View current capacity
python capacity_dashboard.py

# View latest alerts
cat ~/Scripts/StudioProcesses/capacity_alerts.txt

# View detailed logs
tail -50 ~/Scripts/StudioProcesses/video_scorer.log

# Check audit log
grep "OVER" ~/Scripts/StudioProcesses/manipulation_audit.log

# Force run scoring (instead of waiting for cron)
source venv/bin/activate && python video_scorer.py

# Force run timeline script
source myenv/bin/activate && python production_timeline.py
```

---

## 🎯 What to Do When Someone is Over Capacity

1. **Review the task list** in the capacity dashboard
2. **Options:**
   - Delay lower-priority tasks
   - Reassign tasks to someone with available capacity
   - Adjust project timelines to spread the workload
   - Mark tasks as completed if done
3. **The system updates automatically** every 15 minutes

---

## 📞 Support

For issues or questions:
- Check logs: `~/Scripts/StudioProcesses/video_scorer.log`
- Review this guide
- Test manually: `python capacity_dashboard.py`
