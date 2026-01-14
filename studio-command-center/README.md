# 🎬 Studio Command Center

An interactive, real-time monitoring dashboard for Perimeter Studio operations.

## Features

✅ **Real-time Status Board** - Key metrics at a glance
✅ **Team Capacity Monitoring** - See who's available and who's overloaded
✅ **At-Risk Task Alerts** - Instant visibility into potential issues
✅ **Upcoming Events** - Shoots and deadlines in one view
✅ **Auto-refresh** - Stays current with Asana data
✅ **Mobile Responsive** - Works on any device
✅ **Space-themed UI** - Matches your existing dashboard aesthetic

---

## Quick Start

### Option 1: Development Mode (Recommended for testing)

**Terminal 1 - Start Backend API:**
```bash
cd backend
./start.sh
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Then open: **http://localhost:3000**

---

### Option 2: Production Build

**Build and serve:**
```bash
./build-and-serve.sh
```

Then open: **http://localhost:5000**

---

## Architecture

```
studio-command-center/
├── backend/          # Flask API server
│   ├── app.py       # Main API endpoints
│   └── start.sh     # Backend startup script
│
└── frontend/        # React application
    ├── src/
    │   ├── App.jsx          # Main app component
    │   ├── components/      # UI components
    │   │   ├── Header.jsx
    │   │   ├── StatusBoard.jsx
    │   │   ├── TeamCapacity.jsx
    │   │   ├── AtRiskTasks.jsx
    │   │   └── UpcomingEvents.jsx
    │   └── styles/          # CSS files
    └── package.json
```

---

## API Endpoints

### `GET /api/status`
Health check endpoint

### `GET /api/dashboard`
Complete dashboard data including:
- Metrics summary
- Team capacity
- At-risk tasks
- Upcoming shoots/deadlines
- Categories
- Delivery metrics

### `GET /api/refresh`
Force refresh data from Asana

### `GET /api/team`
Team capacity data only

### `GET /api/at-risk`
At-risk tasks only

---

## Features

### Auto-Refresh
- Automatically refreshes every 2 minutes
- Toggle on/off with button in header
- Manual refresh button always available

### Smart Caching
- Backend caches data for 5 minutes
- Reduces Asana API calls
- Force refresh with `/api/refresh` endpoint

### Responsive Design
- Desktop: Full dashboard grid
- Tablet: Adaptive layout
- Mobile: Stacked single column

### Status Indicators
- 🟢 Normal: < 80% capacity
- 🟡 High: 80-100% capacity
- 🔴 Overloaded: > 100% capacity

---

## Customization

### Update Refresh Interval

Edit `frontend/src/App.jsx`:
```javascript
const interval = setInterval(() => {
  fetchData()
}, 120000) // Change to desired milliseconds
```

### Update Cache Duration

Edit `backend/app.py`:
```python
cache = {
    'cache_duration': 300  # Change to desired seconds
}
```

### Modify Colors

Edit `frontend/src/styles/App.css`:
```css
:root {
  --color-accent: #60BBE9;  /* Change primary color */
  --color-success: #4ecca3; /* Change success color */
  /* ... etc */
}
```

---

## Deployment

### Local Server
The app runs on your local machine at:
- Backend: `http://localhost:5000`
- Frontend (dev): `http://localhost:3000`

### Production Deployment Options

**Option 1: Same Server as Current Dashboard**
```bash
./build-and-serve.sh
# Access at http://localhost:5000
```

**Option 2: Cloud Hosting (Vercel, Netlify, etc.)**
- Build frontend: `cd frontend && npm run build`
- Deploy `frontend/dist` folder
- Set up backend API separately

**Option 3: Docker**
Create `Dockerfile` for containerized deployment

---

## Troubleshooting

### "Cannot connect to API"
- Make sure backend is running (`cd backend && ./start.sh`)
- Check that port 5000 isn't already in use

### "Module not found" errors
```bash
cd frontend
npm install
```

### "Permission denied" on start.sh
```bash
chmod +x backend/start.sh
chmod +x build-and-serve.sh
```

### Data not updating
- Click the "Refresh" button to force update
- Check backend logs for Asana API errors
- Verify `.env` file has correct Asana credentials

---

## Next Steps / Future Enhancements

🚀 **Phase 2 Ideas:**
- [ ] Interactive filtering (by project, team member, date range)
- [ ] Click-to-drill-down charts
- [ ] Real-time WebSocket updates (no polling)
- [ ] Task completion from dashboard
- [ ] Team notifications/alerts
- [ ] Historical trend graphs
- [ ] Export reports feature
- [ ] Mobile app (React Native)

---

## Tech Stack

**Frontend:**
- React 18
- Vite (build tool)
- Recharts (charting library)
- date-fns (date formatting)

**Backend:**
- Python 3
- Flask (web framework)
- Flask-CORS

**Data Source:**
- Existing `generate_dashboard.py` Asana integration

---

## Support

Questions or issues? Check the logs:
- Backend: `backend/logs/` (if configured)
- Frontend dev: Terminal output
- Browser: DevTools Console (F12)

---

**Built with Claude Code** 🤖
