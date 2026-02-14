#!/bin/bash

# Studio Dashboard - Railway Deployment Script
# This script helps set up and deploy the Studio Dashboard to Railway

set -e

echo "🚀 Studio Dashboard - Railway Deployment Setup"
echo "=============================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "📦 Install it with: npm install -g @railway/cli"
    echo "🔗 Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

echo "✅ Railway CLI found"

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway:"
    railway login
fi

echo "✅ Railway authentication verified"

# Check required files exist
required_files=(
    "Procfile"
    "railway.json"
    "requirements.txt"
    "main.py"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All deployment files present"

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "⚠️  No .env file found. Copy .env.example to .env and configure:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your API keys and configuration"
    echo ""
    read -p "Continue without .env file? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Initialize Railway project if not already done
if [[ ! -f "railway.toml" ]] && [[ ! -d ".railway" ]]; then
    echo "🆕 Initializing new Railway project..."
    railway init
else
    echo "✅ Railway project already initialized"
fi

# Set environment variables from .env if it exists
if [[ -f ".env" ]]; then
    echo "📝 Setting environment variables..."

    # Read .env and set variables (skip comments and empty lines)
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi

        # Extract key=value pairs
        if [[ $line =~ ^([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"

            # Set the environment variable in Railway
            echo "Setting $key..."
            railway variables set "$key=$value"
        fi
    done < .env

    echo "✅ Environment variables configured"
fi

# Add volume for Reports directory
echo "💾 Setting up persistent volume for Reports directory..."
echo "🔧 You need to manually create a volume in Railway dashboard:"
echo "   1. Go to your Railway project dashboard"
echo "   2. Click on your service"
echo "   3. Go to 'Volumes' tab"
echo "   4. Create new volume:"
echo "      - Name: reports-storage"
echo "      - Mount Path: /app/Reports"
echo "      - Size: 1GB (or as needed)"
echo ""

read -p "Press Enter when volume is created..."

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📱 Your app will be available at:"
railway domain

echo ""
echo "🔍 Useful commands:"
echo "   railway logs     - View application logs"
echo "   railway shell    - Access app shell"
echo "   railway status   - Check deployment status"
echo ""
echo "🔗 Dashboard endpoints:"
echo "   /health         - Health check"
echo "   /docs          - API documentation"
echo "   /              - Studio Dashboard"
echo ""
echo "✅ Setup complete! Check your Railway dashboard for final configuration."