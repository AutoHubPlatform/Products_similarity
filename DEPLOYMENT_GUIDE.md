# Step-by-Step Deployment Guide

## Option 1: Using the Manual Deployment Script

1. **Update the server address in deploy-manual.sh:**
   ```bash
   # Edit the REMOTE_SERVER variable with your actual server IP
   REMOTE_SERVER="hazem@YOUR_ACTUAL_SERVER_IP"
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy-manual.sh
   ```

## Option 2: Manual Commands (if you know the server IP)

Replace `YOUR_SERVER_IP` with your actual server IP address:

1. **Create deployment package:**
   ```bash
   cd /home/hazem-elbatawy/Downloads/Gpt_Erp_prod_version
   tar -czf image-matcher-deploy.tar.gz app/ db/ docker-compose.yml README.md clip_embedder.py
   ```

2. **Copy files to remote server:**
   ```bash
   scp image-matcher-deploy.tar.gz hazem@YOUR_SERVER_IP:/home/hazem/
   ```

3. **Connect to remote server and extract:**
   ```bash
   ssh hazem@YOUR_SERVER_IP
   cd /home/hazem/maxQ.hyperautomation/backend/services/image-matcher
   tar -xzf /home/hazem/image-matcher-deploy.tar.gz
   ```

4. **Build and start Docker containers:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Option 3: Using rsync directly (if you know the server IP)

```bash
cd /home/hazem-elbatawy/Downloads/Gpt_Erp_prod_version
rsync -avz --delete \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  ./ hazem@YOUR_SERVER_IP:/home/hazem/maxQ.hyperautomation/backend/services/image-matcher/
```

## Troubleshooting Server Connection

If you're having trouble with the hostname `v2202505272791339866`, try:

1. **Find the actual IP address:**
   ```bash
   nslookup v2202505272791339866
   # or
   ping v2202505272791339866
   ```

2. **Check your SSH config (~/.ssh/config):**
   ```
   Host myserver
       HostName YOUR_ACTUAL_IP_OR_DOMAIN
       User hazem
       Port 22
   ```

3. **Test direct IP connection:**
   ```bash
   ssh hazem@ACTUAL_IP_ADDRESS
   ```

## After Deployment

1. **Check container status:**
   ```bash
   ssh hazem@YOUR_SERVER_IP 'cd /home/hazem/maxQ.hyperautomation/backend/services/image-matcher && docker-compose ps'
   ```

2. **View logs:**
   ```bash
   ssh hazem@YOUR_SERVER_IP 'cd /home/hazem/maxQ.hyperautomation/backend/services/image-matcher && docker-compose logs'
   ```

3. **Access the application:**
   - Open browser: `http://YOUR_SERVER_IP:8501`
