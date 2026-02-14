# 📺 Raspberry Pi TV Display Setup Guide

## Quick Setup (3 Steps)

### On Your Mac (Already Done ✅)
- Servers are running and accessible at: **http://172.16.28.50:3000**
- Backend and frontend configured for network access

### On Your Raspberry Pi

**Step 1:** Copy the setup script to your Pi

```bash
# Option A: Use USB drive
# Copy setup-pi-display.sh to a USB drive, then on Pi:
cp /media/usb/setup-pi-display.sh ~/
chmod +x ~/setup-pi-display.sh

# Option B: Download directly (if Pi has internet)
# You could host it temporarily or type it out
```

**Step 2:** Run the setup script
```bash
cd ~
./setup-pi-display.sh
```

**Step 3:** Reboot when prompted
```bash
# The script will ask if you want to reboot
# Choose 'y' to reboot now
```

That's it! After reboot, your TV will show the dashboard in full-screen kiosk mode.

---

## What This Does

✅ **Hides Everything:**
- No menu bars
- No browser UI
- No cursor (hides after 0.1 seconds)
- No error dialogs

✅ **Prevents Sleep:**
- Screen never blanks
- No screensaver
- Always on display

✅ **Auto-starts:**
- Launches on boot
- No manual interaction needed
- Restarts if browser crashes

✅ **Updates Automatically:**
- Dashboard auto-refreshes every 2 minutes
- Always shows latest data from Asana

---

## Important Notes

### Keep Your Mac Running
- The Pi just displays the dashboard
- Mac must be ON and on the same network
- Servers run on your Mac at ports 3000 (frontend) and 5001 (backend)

### If Mac IP Changes
Your Mac's current IP is **172.16.28.50**. If this changes (restart, network change):

**On Pi, edit the config:**
```bash
nano ~/.config/autostart/studio-dashboard.desktop
```

Update the IP in the URL and reboot.

---

## Troubleshooting

### Dashboard not loading on Pi?
1. Check Mac is on and servers are running
2. Test from Pi terminal: `curl http://172.16.28.50:3000`
3. Make sure both devices on same WiFi network
4. Check Mac's firewall isn't blocking port 3000

### Want to exit kiosk mode on Pi?
- Press `Alt + F4` to close browser
- Or: `Ctrl + Alt + F1` to switch to terminal, then `sudo reboot`

### Menu bar still showing?
- Make sure you ran the script and rebooted
- The `--kiosk` flag should hide everything
- Check the autostart file was created: `cat ~/.config/autostart/studio-dashboard.desktop`

### Mouse cursor not hiding?
- Package `unclutter` might not be installed
- Run: `sudo apt-get install unclutter`
- Then reboot

---

## Manual Control

If you need to start/stop manually:

**Start dashboard:**
```bash
~/launch-dashboard.sh
```

**Stop dashboard:**
```bash
pkill chromium
```

**Prevent auto-start:**
```bash
rm ~/.config/autostart/studio-dashboard.desktop
```

**Re-enable auto-start:**
```bash
./setup-pi-display.sh
# Choose 'n' when asked to reboot, it just recreates the file
```

---

## Files Created on Pi

- `~/.config/autostart/studio-dashboard.desktop` - Auto-start config
- `~/.config/lxsession/LXDE-pi/autostart` - Screen settings
- `~/launch-dashboard.sh` - Manual launch script
- `~/setup-pi-display.sh` - This setup script (can delete after)
