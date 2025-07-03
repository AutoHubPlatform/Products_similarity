#!/bin/bash

# Manual deployment script for the image-matcher application
# This script helps deploy the application to the remote server

# Configuration - UPDATE THESE VALUES
REMOTE_SERVER="hazem@your-server-ip"  # Replace with actual IP address
REMOTE_PATH="/home/hazem/maxQ.hyperautomation/backend/services/image-matcher"
LOCAL_PATH="$(pwd)"

echo "🚀 Starting manual deployment to remote server..."
echo "📝 Please ensure you have updated the REMOTE_SERVER variable with the correct IP address"

# Check if we have the correct server address
if [[ "$REMOTE_SERVER" == *"your-server-ip"* ]]; then
    echo "❌ Please update the REMOTE_SERVER variable in this script with your actual server IP address"
    echo "   Current value: $REMOTE_SERVER"
    echo "   Example: REMOTE_SERVER=\"hazem@192.168.1.100\""
    exit 1
fi

echo "📦 Preparing deployment package..."

# Create a temporary deployment directory
TEMP_DIR="/tmp/image-matcher-deploy-$(date +%s)"
mkdir -p "$TEMP_DIR"

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
echo "   Target: $REMOTE_SERVER:$REMOTE_PATH"

# Test SSH connection first
echo "🔍 Testing SSH connection..."
if ssh -o ConnectTimeout=10 "$REMOTE_SERVER" "echo 'SSH connection successful'"; then
    echo "✅ SSH connection test passed"
else
    echo "❌ SSH connection failed. Please check:"
    echo "   1. Server IP address is correct"
    echo "   2. SSH key is properly configured"
    echo "   3. Server is accessible"
    exit 1
fi

# Create remote directory if it doesn't exist
ssh "$REMOTE_SERVER" "mkdir -p $REMOTE_PATH"

# Upload files using rsync
echo "📂 Syncing files..."
rsync -avz --delete "$TEMP_DIR/" "$REMOTE_SERVER:$REMOTE_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ Files uploaded successfully"
else
    echo "❌ File upload failed"
    exit 1
fi

echo "🐳 Building and starting Docker containers on remote server..."

# Build and start the application on remote server
ssh "$REMOTE_SERVER" << EOL
cd $REMOTE_PATH
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

echo "Building new images..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

echo "Checking container status..."
docker-compose ps

echo "Waiting for services to be ready..."
sleep 15

echo "Testing application connectivity..."
curl -I http://localhost:8501 2>/dev/null || echo "Application may still be starting up..."

echo "✅ Deployment completed!"
echo "🌐 Application should be available at: http://your-server-ip:8501"
EOL

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo "🧹 Cleanup completed"
echo "🎉 Deployment script finished!"
echo ""
echo "📝 Next steps:"
echo "   1. Check the application logs: ssh $REMOTE_SERVER 'cd $REMOTE_PATH && docker-compose logs'"
echo "   2. Access the application at: http://your-server-ip:8501"
