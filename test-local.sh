#!/bin/bash

# Local testing script for the cloned image-matcher application

echo "🧪 Starting local testing environment for the cloned project..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Please activate your virtual environment first:"
    echo "   source .venv/bin/activate"
    exit 1
fi

# Configuration
LOCAL_DB_PORT=5435
APP_PORT=8503

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🗄️ Setting up local test database..."

# Stop and remove any existing test database
docker rm -f test-postgres-clone 2>/dev/null || true

# Start PostgreSQL with pgvector
docker run -d \
    --name test-postgres-clone \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=fruits \
    -p $LOCAL_DB_PORT:5432 \
    ankane/pgvector

echo "⏳ Waiting for database to be ready..."
sleep 8

# Initialize database
echo "🏗️ Initializing database schema..."
docker exec -i test-postgres-clone psql -U postgres -d fruits < db/init.sql

echo "📦 Installing Python dependencies (if needed)..."
pip install -q streamlit psycopg2-binary torch torchvision pillow open_clip_torch openai fastapi uvicorn

echo "🚀 Starting Streamlit application..."

# Set environment variables and start the app
export DB_HOST=localhost
export DB_PORT=$LOCAL_DB_PORT
export DB_NAME=fruits
export DB_USER=postgres
export DB_PASSWORD=postgres

cd app

echo "✅ Starting application on http://localhost:$APP_PORT"
echo "🛑 Press Ctrl+C to stop the application"

# Start Streamlit
python -m streamlit run streamlit_app.py --server.port=$APP_PORT

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    docker rm -f test-postgres-clone 2>/dev/null || true
    echo "✅ Cleanup completed"
}

# Set trap to cleanup on script exit
trap cleanup EXIT
