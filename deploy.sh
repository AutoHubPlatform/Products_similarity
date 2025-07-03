#!/bin/bash

# Deployment script for the cloned image-matcher application
# This script helps deploy the application to the remote server

# Configuration
REMOTE_SERVER="hazem@v2202505272791339866"
REMOTE_PATH="/home/hazem/maxQ.hyperautomation/backend/services/image-matcher"
LOCAL_PATH="$(pwd)"

echo "🚀 Starting deployment to remote server..."

# Create a temporary deployment directory
TEMP_DIR="/tmp/image-matcher-deploy-$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📦 Preparing deployment package..."

# Copy necessary files to temp directory
cp -r "$LOCAL_PATH/app" "$TEMP_DIR/"
cp -r "$LOCAL_PATH/db" "$TEMP_DIR/"
cp "$LOCAL_PATH/docker-compose.yml" "$TEMP_DIR/"
cp "$LOCAL_PATH/README.md" "$TEMP_DIR/"
cp "$LOCAL_PATH/clip_embedder.py" "$TEMP_DIR/"

# Copy .streamlit directory if it exists
if [ -d "$LOCAL_PATH/.streamlit" ]; then
    cp -r "$LOCAL_PATH/.streamlit" "$TEMP_DIR/"
fi

# Create a .env file for production settings
cat > "$TEMP_DIR/.env" << EOL
# Production Environment Variables
DB_HOST=db
DB_PORT=5432
DB_NAME=fruits
DB_USER=postgres
DB_PASSWORD=postgres
PYTHONUNBUFFERED=1
EOL

echo "📤 Uploading files to remote server..."

# Create remote directory if it doesn't exist
ssh "$REMOTE_SERVER" "mkdir -p $REMOTE_PATH"

# Upload files using rsync
rsync -avz --delete "$TEMP_DIR/" "$REMOTE_SERVER:$REMOTE_PATH/"

echo "🐳 Building and starting Docker containers on remote server..."

# Build and start the application on remote server
ssh "$REMOTE_SERVER" << EOL
cd $REMOTE_PATH
echo "Stopping existing containers..."
docker-compose down || true

echo "Building new images..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

echo "Checking container status..."
docker-compose ps

echo "Waiting for services to be ready..."
sleep 15

echo "Testing application connectivity..."
curl -I http://localhost:8501 || echo "Application may still be starting up..."

echo "✅ Deployment completed!"
echo "🌐 Application should be available at: http://your-server-ip:8501"
EOL

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo "🧹 Cleanup completed"
echo "🎉 Deployment script finished!"
