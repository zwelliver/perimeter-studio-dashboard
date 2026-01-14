# GitHub Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `perimeter-studio-dashboard` (or your choice)
3. Description: "Perimeter Studio Capacity Dashboard - Real-time video production capacity tracking"
4. Choose **Private** or **Public** (public allows GitHub Pages)
5. **Do NOT** initialize with README (we already have one)
6. Click "Create repository"

## Step 2: Push Your Code

After creating the repository, GitHub will show you commands. Run these:

```bash
cd ~/Scripts/StudioProcesses

# Add the remote (replace with your GitHub username/org)
git remote add origin https://github.com/YOUR-USERNAME/perimeter-studio-dashboard.git

# Push the code
git branch -M main
git push -u origin main
```

## Step 3: Enable GitHub Pages (Optional - For Live Dashboard URL)

This creates a public URL where others can view the dashboard without downloading:

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Pages** in the left sidebar
4. Under "Source", select **main** branch
5. Select **/ (root)** folder
6. Click **Save**

After a few minutes, your dashboard will be live at:
```
https://YOUR-USERNAME.github.io/perimeter-studio-dashboard/Reports/capacity_dashboard.html
```

## Step 4: Automate Dashboard Updates

Update your cron job to automatically commit and push dashboard updates:

### Create Auto-Commit Script

Create `~/Scripts/StudioProcesses/auto_commit_dashboard.sh`:

```bash
#!/bin/bash
cd ~/Scripts/StudioProcesses

# Check if dashboard was updated
if git diff --quiet Reports/capacity_dashboard.html; then
    echo "No dashboard changes to commit"
    exit 0
fi

# Commit and push the updated dashboard
git add Reports/capacity_dashboard.html
git commit -m "Update capacity dashboard - $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "Dashboard updated on GitHub"
```

Make it executable:
```bash
chmod +x ~/Scripts/StudioProcesses/auto_commit_dashboard.sh
```

### Update Cron Job

Edit your crontab:
```bash
crontab -e
```

Update the cron line to include the auto-commit script:
```bash
*/15 * * * * cd ~/Scripts/StudioProcesses && source venv/bin/activate && python video_scorer.py >> cron_log.txt 2>&1 && ./auto_commit_dashboard.sh >> cron_log.txt 2>&1
```

This will:
1. Run video_scorer.py every 15 minutes (generates dashboard)
2. Auto-commit and push dashboard updates to GitHub
3. Anyone with the GitHub Pages URL sees live updates

## Step 5: Set Up Git Authentication (If Needed)

If git push asks for credentials every time:

### Option A: Personal Access Token (Recommended)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Dashboard Auto-Commit"
4. Select scopes: **repo** (all checkboxes under repo)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

Configure git to use it:
```bash
# Add token to remote URL
git remote set-url origin https://YOUR-TOKEN@github.com/YOUR-USERNAME/perimeter-studio-dashboard.git
```

### Option B: SSH Key (Alternative)

1. Generate SSH key:
```bash
ssh-keygen -t ed25519 -C "your-email@perimeter.org"
```

2. Add to GitHub: https://github.com/settings/ssh/new
3. Change remote to SSH:
```bash
git remote set-url origin git@github.com:YOUR-USERNAME/perimeter-studio-dashboard.git
```

## Sharing the Dashboard

### Public Repository with GitHub Pages
Share this URL:
```
https://YOUR-USERNAME.github.io/perimeter-studio-dashboard/Reports/capacity_dashboard.html
```

### Private Repository
Options for sharing:
1. **Add collaborators** - Settings → Collaborators → Add people
2. **Download and share** - Download HTML file and email/share via drive
3. **Make repo public** - Settings → Danger Zone → Change visibility

## Troubleshooting

### Dashboard not updating on GitHub Pages
- Check if commit was successful: `git log`
- Check GitHub Actions tab for build errors
- GitHub Pages can take 1-2 minutes to update after push

### Authentication failures
- Verify your personal access token is correct
- Ensure token has `repo` scope
- Check remote URL: `git remote -v`

### Cron job not running
- Check cron logs: `tail ~/Scripts/StudioProcesses/cron_log.txt`
- Verify script has execute permissions: `ls -l auto_commit_dashboard.sh`
- Test manually: `./auto_commit_dashboard.sh`

## Security Note

The `.gitignore` file prevents committing:
- `.env` files (API keys)
- CSV reports with sensitive data
- Log files
- Python cache files

Only the dashboard HTML is committed, which contains aggregate metrics without sensitive details.
