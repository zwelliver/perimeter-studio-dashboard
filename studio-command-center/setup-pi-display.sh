#!/bin/bash
# Studio Command Center - Raspberry Pi TV Display Setup
# Run this script on your Raspberry Pi

echo "🖥️  Setting up Studio Command Center TV Display..."

# Your Mac's IP (update if it changes)
MAC_IP="172.16.28.50"
DASHBOARD_URL="http://$MAC_IP:3000"

# 1. Install required packages
echo "📦 Installing required packages..."
sudo apt-get update
sudo apt-get install -y chromium-browser unclutter xdotool

# 2. Disable screensaver and screen blanking
echo "⚙️  Disabling screensaver..."
mkdir -p ~/.config/lxsession/LXDE-pi
cat > ~/.config/lxsession/LXDE-pi/autostart << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@point-rpi
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
EOF

# 3. Create kiosk mode autostart
echo "🚀 Setting up auto-start..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/studio-dashboard.desktop << EOF
[Desktop Entry]
Type=Application
Name=Studio Command Center
Exec=/usr/bin/chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state --disable-features=TranslateUI --no-first-run --fast --fast-start --disable-popup-blocking --disable-translate --app=$DASHBOARD_URL
X-GNOME-Autostart-enabled=true
Hidden=false
EOF

# 4. Hide mouse cursor when idle
echo "🖱️  Configuring cursor auto-hide..."

# 5. Create manual launch script
cat > ~/launch-dashboard.sh << EOF
#!/bin/bash
# Quick launch script (if you need to start manually)
chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars --app=$DASHBOARD_URL
EOF
chmod +x ~/launch-dashboard.sh

# 6. Test connection
echo "🔍 Testing connection to Mac..."
if curl -s --connect-timeout 5 "$DASHBOARD_URL" > /dev/null; then
    echo "✅ Successfully connected to dashboard at $DASHBOARD_URL"
else
    echo "⚠️  Warning: Cannot reach $DASHBOARD_URL"
    echo "   Make sure your Mac is on and both devices are on the same network"
    echo "   Mac IP: $MAC_IP"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 What happens now:"
echo "   • Screen will never sleep or show screensaver"
echo "   • Mouse cursor hides after 0.1 seconds of inactivity"
echo "   • Dashboard launches automatically on boot"
echo "   • All menu bars and UI elements are hidden"
echo ""
echo "🔧 Options:"
echo "   1. Reboot now: sudo reboot"
echo "   2. Test manually: ~/launch-dashboard.sh"
echo ""
echo "💡 If Mac IP changes, edit this file:"
echo "   nano ~/.config/autostart/studio-dashboard.desktop"
echo "   (Change the IP in the Exec line)"
echo ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
