# Railway Deployment Guide - Studio Dashboard

This guide covers deploying the Studio Dashboard to Railway.app.

## Files Created

### Core Deployment Files

1. **`Procfile`** - Defines the web process command
2. **`railway.json`** - Railway configuration with build commands and volume mounting
3. **`nixpacks.toml`** - Build configuration for Python + Node.js
4. **`requirements.txt`** - Python dependencies for FastAPI backend
5. **`.env.example`** - Environment variables template
6. **`.dockerignore`** - Files to exclude from build context

### Application Files

- **`main.py`** - FastAPI application entry point
- **`app/`** - Application modules (config, routers, services)

## Deployment Steps

### 1. Prepare Your Railway Project

1. Sign up at [railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values, then add these to Railway:

**Required Variables:**
```
ENVIRONMENT=production
ASANA_PAT_SCORER=your_asana_token
ASANA_PAT_BACKDROP=your_asana_token
FILM_DATE_FIELD_GID=your_field_id
TASK_PROGRESS_FIELD_GID=your_field_id
NEEDS_SCHEDULING_OPTION_GID=your_option_id
PRODUCTION_PROJECT_GIDS=comma,separated,ids
```

**Optional Variables:**
```
CACHE_DURATION=3600
LOG_LEVEL=INFO
SMTP_SERVER=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Set Up Persistent Storage

The dashboard needs persistent storage for the `Reports/` directory:

1. In Railway dashboard, go to your service
2. Go to "Volumes" tab
3. Create a new volume:
   - **Name**: `reports-storage`
   - **Mount Path**: `/app/Reports`
   - **Size**: 1GB (adjust as needed)

### 4. Deploy

1. Push your code to GitHub
2. Railway will automatically detect the configuration and deploy
3. The build process will:
   - Install Python dependencies
   - Install Node.js dependencies
   - Build the React frontend
   - Start the FastAPI server

### 5. Verify Deployment

Once deployed, check:

- **Health Check**: `https://your-app.railway.app/health`
- **API Docs**: `https://your-app.railway.app/docs`
- **Dashboard**: `https://your-app.railway.app/`

## Build Process

The deployment uses a multi-stage build:

1. **Python Setup**: Install Python 3.11 and dependencies
2. **Node.js Setup**: Install Node.js 18 and build frontend
3. **Start Server**: Run uvicorn with FastAPI app

## Architecture

```
Railway Container
├── Python 3.11 + FastAPI backend
├── Node.js 18 (build only)
├── Frontend: React SPA (built to dist/)
├── Volume: /app/Reports (persistent)
└── Port: $PORT (dynamic)
```

## Configuration Details

### Procfile
Defines the web process that Railway will run:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### railway.json
- **Build Command**: Installs both Python and Node dependencies, builds frontend
- **Volumes**: Mounts persistent storage for Reports directory
- **Environment**: Supports multiple environments (production/staging)

### nixpacks.toml
- **Providers**: Python 3.11 + Node.js 18
- **Phases**: setup → install → build → start
- **Variables**: Optimizes Python package installation

## Monitoring

### Health Endpoint
```
GET /health
Response: {"status": "healthy", "environment": "production"}
```

### Logs
Access logs via Railway dashboard or CLI:
```bash
railway logs
```

## Troubleshooting

### Build Failures

1. **Python dependencies**: Check `requirements.txt` versions
2. **Node.js build**: Ensure `package.json` scripts are correct
3. **File permissions**: Check file paths in `main.py`

### Runtime Issues

1. **Environment variables**: Verify all required vars are set
2. **Volume mounting**: Check `/app/Reports` directory exists
3. **Port binding**: Ensure app binds to `$PORT`

### Frontend Not Loading

1. Check build output in `/studio-command-center/frontend/dist/`
2. Verify static file mounting in `main.py`
3. Check frontend routing configuration

## Scaling

Railway automatically handles:
- **Load balancing**: Multiple instances behind load balancer
- **Autoscaling**: Based on CPU/memory usage
- **Health checks**: Automatic restart on failures

## Security

- Environment variables are encrypted
- HTTPS is automatic on Railway domains
- Secrets are not included in build logs
- Volume data is isolated per service

## Cost Optimization

- **Starter Plan**: $5/month for basic usage
- **Volume Storage**: Charged per GB/month
- **Bandwidth**: Included allowances with plans
- **Build Minutes**: Optimize build time to reduce usage