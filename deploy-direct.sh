#!/bin/bash

# Direct deployment script for the image-matcher application
# This script directly syncs files to the remote server without compression

# Configuration
REMOTE_SERVER="automationhub-server"  # Using SSH config alias
REMOTE_PATH="/home/hazem/maxQ.hyperautomation/backend/services/image-matcher"
LOCAL_PATH="$(pwd)"

echo "🚀 Starting direct deployment to remote server..."

echo "📤 Syncing files directly to remote server..."

# Sync files directly using rsync
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='build.log' \
  --exclude='=0.79.0' \
  --exclude='.streamlit' \
  "$LOCAL_PATH/" "$REMOTE_SERVER:$REMOTE_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ Files synced successfully"
else
    echo "❌ File sync failed"
    exit 1
fi

echo "🐳 Building and starting Docker containers on remote server..."

# Build and start the application on remote server
ssh "$REMOTE_SERVER" << 'EOL'
cd /home/hazem/maxQ.hyperautomation/backend/services/image-matcher

echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

echo "Building new images..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

echo "Checking container status..."
docker-compose ps

echo "✅ Deployment completed!"
echo "🌐 Application should be available at port 8501"
EOL

echo "🎉 Direct deployment finished!"
