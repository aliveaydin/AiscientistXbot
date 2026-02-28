#!/bin/bash
# ============================================
# AiScientist X Bot - VPS Setup Script
# Run this on a fresh Hetzner VPS (Ubuntu 24.04)
# ============================================

set -e

echo "🤖 Setting up AiScientist X Bot..."

# 1. Update system
echo "📦 Updating system..."
apt-get update && apt-get upgrade -y

# 2. Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 3. Install Docker Compose
echo "🔧 Installing Docker Compose..."
apt-get install -y docker-compose-plugin

# 4. Create app directory
echo "📁 Creating app directory..."
mkdir -p /opt/aiscientist-bot
cd /opt/aiscientist-bot

# 5. Clone the repo
echo "📥 Cloning repository..."
git clone https://github.com/aliveaydin/AiscientistXbot.git .

# 6. Create .env.production file
echo "⚙️ Creating environment file..."
cat > .env.production << 'ENVEOF'
# === FILL IN YOUR KEYS ===
TWITTER_API_KEY=YOUR_KEY_HERE
TWITTER_API_SECRET=YOUR_SECRET_HERE
TWITTER_ACCESS_TOKEN=YOUR_TOKEN_HERE
TWITTER_ACCESS_TOKEN_SECRET=YOUR_TOKEN_SECRET_HERE
TWITTER_BEARER_TOKEN=YOUR_BEARER_HERE
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE

# Bot Settings
DEFAULT_AI_MODEL=claude-sonnet-4-20250514
TWEET_INTERVAL_MINUTES=120
AUTO_REPLY_ENABLED=true
ENVEOF

echo ""
echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the env file:  nano /opt/aiscientist-bot/.env.production"
echo "2. Fill in your API keys"
echo "3. Start the bot:  docker compose up -d --build"
echo "4. Check logs:     docker compose logs -f"
echo "5. Dashboard:      http://YOUR_SERVER_IP"
echo "============================================"
