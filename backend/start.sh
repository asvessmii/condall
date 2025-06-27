
#!/bin/bash

# Start FastAPI server in the background
uvicorn server:app --host 0.0.0.0 --port 8001 &

# Start Telegram bot
python3 telegram_admin.py

# Keep the script running to keep both processes alive
wait


