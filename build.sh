#!/bin/bash
set -e

echo "=== Studio Dashboard Build Script ==="

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build React frontend
echo "🏗️ Building React frontend..."
cd studio-command-center/frontend

echo "📦 Installing Node.js dependencies..."
npm install

echo "🎯 Building React application..."
npm run build

echo "✅ Build completed successfully!"
echo "📁 Frontend built to: studio-command-center/frontend/dist/"

# List build output for verification
echo "📋 Build output contents:"
ls -la dist/

echo "=== Build Complete ==="