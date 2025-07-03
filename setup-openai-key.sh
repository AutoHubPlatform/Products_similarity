#!/bin/bash

# ================================================================================
# OpenAI API Key Setup Script for AI Product Recognition System
# ================================================================================
# 
# INSTRUCTIONS FOR CLIENT:
# 1. Edit this script and add your OpenAI API key in the OPENAI_KEY variable below
# 2. Replace the empty quotes with your actual API key (without quotes around the key)
# 3. Run this script: ./setup-openai-key.sh
# 4. The API key will be permanently added to your Docker environment
#
# Example:
# OPENAI_KEY="sk-proj-your-actual-api-key-here"
#
# ================================================================================

echo "🔑 Adding OpenAI API key permanently to Docker environment..."

# Your OpenAI API key - EDIT THIS LINE:
OPENAI_KEY=""

# Validation check
if [ -z "$OPENAI_KEY" ]; then
    echo "❌ ERROR: Please edit this script and add your OpenAI API key to the OPENAI_KEY variable"
    echo "📝 Example: OPENAI_KEY=\"sk-proj-your-actual-api-key-here\""
    echo "💡 Then run this script again: ./setup-openai-key.sh"
    exit 1
fi

# Step 1: Stop the application
echo "⏹️ Stopping application..."
docker-compose down

# Step 2: Backup the original docker-compose.yml
echo "💾 Creating backup of docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.backup

# Step 3: Add the API key to the app environment in docker-compose.yml
echo "⚙️ Adding OpenAI API key to docker-compose.yml..."

# Use sed to add the OPENAI_API_KEY to the app service environment section
sed -i '/environment:/a\      OPENAI_API_KEY: "'$OPENAI_KEY'"' docker-compose.yml

# Alternative: If the above doesn't work, we'll replace the entire environment section
if ! grep -q "OPENAI_API_KEY" docker-compose.yml; then
    echo "🔧 Using alternative method to add API key..."
    
    # Create a temporary file with the updated environment section
    cat > temp_env.txt << EOL
    environment:
      DB_HOST: db
      DB_PORT: "5432"
      DB_NAME: fruits
      DB_USER: postgres
      DB_PASSWORD: postgres
      PYTHONUNBUFFERED: "1"
      OPENAI_API_KEY: "$OPENAI_KEY"
EOL
    
    # Replace the environment section in docker-compose.yml
    sed -i '/environment:/,/working_dir:/{/environment:/!{/working_dir:/!d}}' docker-compose.yml
    sed -i '/environment:/r temp_env.txt' docker-compose.yml
    sed -i '/environment:/d' docker-compose.yml
    
    # Clean up
    rm temp_env.txt
fi

# Step 4: Verify the change was made
echo "🔍 Verifying API key was added..."
if grep -q "OPENAI_API_KEY" docker-compose.yml; then
    echo "✅ OpenAI API key successfully added to docker-compose.yml"
else
    echo "❌ Failed to add API key automatically. Manual edit required."
    echo "Please manually add this line under the app service environment section:"
    echo "      OPENAI_API_KEY: \"$OPENAI_KEY\""
    exit 1
fi

# Step 5: Start the application
echo "🚀 Starting application with OpenAI API key..."
docker-compose up -d

# Step 6: Check if containers are running
echo "⏳ Waiting for containers to start..."
sleep 10

echo "📊 Checking container status..."
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo "🌐 Your application with OpenAI integration is available at: http://46.232.249.36:8501"
echo "🔑 OpenAI API key is now permanently configured"
echo ""
echo "📝 Notes:"
echo "- A backup of your original docker-compose.yml was saved as docker-compose.yml.backup"
echo "- The API key is now part of the Docker environment and will persist across restarts"
echo "- No need to manually set the API key anymore!"
