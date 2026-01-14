# 🚀 Quick Start Guide

## Get Your Studio Command Center Running in 2 Minutes!

### Step 1: Open Two Terminal Windows

### Step 2: Start the Backend (Terminal 1)
```bash
cd /Users/comstudio/Scripts/StudioProcesses/studio-command-center/backend
./start.sh
```

You'll see:
```
🎬 Studio Command Center API Starting...
📡 API will be available at: http://localhost:5000
```

**Keep this terminal running!**

---

### Step 3: Start the Frontend (Terminal 2)
```bash
cd /Users/comstudio/Scripts/StudioProcesses/studio-command-center/frontend
npm install  # Only needed first time
npm run dev
```

You'll see:
```
VITE ready in XXX ms
Local: http://localhost:3000
```

---

### Step 4: Open Your Browser
Go to: **http://localhost:3000**

You should see your Studio Command Center with:
- ✅ Live status metrics
- 👥 Team capacity bars
- ⚠️ At-risk tasks
- 📅 Upcoming shoots and deadlines

---

## 🎯 What You'll See

### Top Row - Status Cards
Four big metric cards showing:
- Active tasks count
- At-risk tasks (with warning color if > 0)
- Upcoming shoots
- Upcoming deadlines

### Second Row - Team Capacity
Horizontal bars for each team member showing:
- Current hours / Max hours
- Utilization percentage
- Color-coded status (green/yellow/red)

### Bottom Row - Two Panels
**Left:** At-Risk Tasks
- Shows tasks that might be in trouble
- Risk factors listed for each

**Right:** Upcoming Events
- Shoots section with film dates
- Deadlines section with due dates
- Color-coded urgency badges

---

## ⚙️ Controls

**Auto-refresh Toggle**
- Enabled by default (refreshes every 2 minutes)
- Click to turn on/off

**Refresh Button**
- Click anytime to get fresh data from Asana
- Shows spinning icon while loading

**Last Updated**
- Shows when data was last refreshed
- Example: "Last updated 3 minutes ago"

---

## 🔧 Troubleshooting

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend errors
- Check that you're in the parent StudioProcesses directory
- Verify `.env` file has Asana credentials
- Make sure port 5000 isn't in use

### "Cannot connect to API"
- Make sure backend terminal is still running
- Check that both terminals are active

### Data looks old
- Click the "Refresh" button
- Check auto-refresh is enabled (green dot)

---

## 💡 Tips

- Leave both terminals running while using the app
- Use `Ctrl+C` in terminal to stop servers
- Frontend has hot-reload - changes appear instantly
- Backend caches data for 5 min to reduce API calls

---

## 📱 Mobile Access

On your phone/tablet:
1. Find your computer's IP address
2. Open `http://YOUR-IP:3000` on mobile
3. Works great on phones and tablets!

---

## What's Next?

The app is fully functional! Some ideas:
- Try it on different devices
- Share URL with your team
- Let it auto-refresh and monitor live
- Use it on a TV display in the studio

Enjoy your new Command Center! 🎬
