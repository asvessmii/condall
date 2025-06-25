#!/bin/bash

# Script to run Telegram Admin Bot
echo "Starting Telegram Admin Bot..."

cd /app/backend

# Activate virtual environment if it exists
if [ -d "/root/.venv" ]; then
    source /root/.venv/bin/activate
fi

# Run the bot
python telegram_admin.py