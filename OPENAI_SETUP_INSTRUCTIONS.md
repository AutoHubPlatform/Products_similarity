# 🔑 OpenAI API Key Setup Instructions

## For Full AI Features (Optional)

Your AI Product Recognition System works without an OpenAI API key, but adding one enables advanced features like automatic product name suggestions and descriptions.

## Option 1: Add API Key via Web Interface (Recommended)
1. Open your application: http://46.232.249.36:8501
2. Look for the "OpenAI API Key" field in the interface
3. Paste your API key (without quotes)
4. Start using AI features immediately!

## Option 2: Add API Key Permanently (Advanced)
If you want the API key to be permanent and not require entering it each time:

### Step 1: Get Your OpenAI API Key
- Go to https://platform.openai.com/api-keys
- Create a new API key if you don't have one
- Copy the key (starts with "sk-proj-...")

### Step 2: Edit the Setup Script
1. Open the file: `setup-openai-key.sh`
2. Find this line: `OPENAI_KEY=""`
3. Add your key between the quotes: `OPENAI_KEY="sk-proj-your-key-here"`
4. Save the file

### Step 3: Run the Setup Script
```bash
chmod +x setup-openai-key.sh
./setup-openai-key.sh
```

The script will:
- ✅ Stop the application safely
- ✅ Add your API key to the Docker environment
- ✅ Restart the application with AI features enabled
- ✅ Create a backup of your configuration

## What AI Features You'll Get:
- 🧠 **Smart Product Naming**: AI suggests product names from images
- 📝 **Auto Descriptions**: Generate product descriptions automatically  
- 🔍 **Enhanced Search**: Better similarity matching with AI understanding
- 📊 **Product Categorization**: AI suggests product categories

## Troubleshooting:
- **API key not working?** Make sure there are no extra spaces or quotes
- **Script fails?** Check that you have the correct permissions and Docker is running
- **Need help?** The web interface method is simpler and works just as well

---
*Note: OpenAI API usage has costs. Check OpenAI's pricing at https://openai.com/pricing*
