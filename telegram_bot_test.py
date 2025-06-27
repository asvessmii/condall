import unittest
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Add backend directory to path to import telegram_admin
sys.path.append('/app/backend')

class TelegramBotChangesTest(unittest.TestCase):
    """Test suite for the Telegram Bot changes"""

    def test_01_telegram_bot_running_as_service(self):
        """Test that Telegram bot is running as a supervisor service"""
        print("\n🔍 Testing Telegram bot supervisor service...")
        
        # Check if telegram_bot service is running
        result = subprocess.run(["sudo", "supervisorctl", "status", "telegram_bot"], 
                               capture_output=True, text=True)
        
        # Check if the service is running
        self.assertIn("RUNNING", result.stdout)
        print(f"✅ Telegram bot is running as a supervisor service: {result.stdout.strip()}")
        
        # Check if the service is configured to auto-restart
        config_result = subprocess.run(["cat", "/etc/supervisor/conf.d/supervisord.conf"], 
                                      capture_output=True, text=True)
        self.assertIn("program:telegram_bot", config_result.stdout)
        self.assertIn("autorestart=true", config_result.stdout)
        print("✅ Telegram bot is configured to auto-restart")

    def test_02_telegram_bot_code_changes(self):
        """Test that the Telegram bot code has the required changes"""
        print("\n🔍 Testing Telegram bot code changes...")
        
        # Check if telegram_admin.py exists
        self.assertTrue(os.path.exists('/app/backend/telegram_admin.py'))
        
        # Read the file content
        with open('/app/backend/telegram_admin.py', 'r') as f:
            content = f.read()
        
        # Check for /start command implementation for regular users
        self.assertIn("async def start_command", content)
        self.assertIn("Добро пожаловать в КЛИМАТ ТЕХНО", content)
        self.assertIn("Открыть каталог", content)
        self.assertIn("Связаться с нами", content)
        print("✅ /start command implementation for regular users found")
        
        # Check for /admin command implementation
        self.assertIn("async def admin_command", content)
        self.assertIn("if not await check_admin(update):", content)
        self.assertIn("Админ панель КЛИМАТ ТЕХНО", content)
        print("✅ /admin command implementation found")
        
        # Check for contact_info button handler
        self.assertIn("contact_info", content)
        self.assertIn("Контактная информация", content)
        print("✅ 'Связаться с нами' button implementation found")
        
        # Check for admin authentication
        self.assertIn("ADMIN_ID", content)
        self.assertIn("У вас нет прав доступа к админ панели", content)
        print("✅ Admin authentication implementation found")

    def test_03_admin_id_configuration(self):
        """Test that the admin ID is correctly configured"""
        print("\n🔍 Testing admin ID configuration...")
        
        # Check if .env file exists
        self.assertTrue(os.path.exists('/app/backend/.env'))
        
        # Read the file content
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        # Check for ADMIN_ID
        self.assertIn("ADMIN_ID", content)
        self.assertIn("7470811680", content)
        print("✅ Admin ID is correctly configured in .env file")
        
        # Import the telegram_admin module to check ADMIN_ID
        try:
            import telegram_admin
            self.assertEqual(telegram_admin.ADMIN_ID, 7470811680)
            print("✅ Admin ID is correctly loaded in the telegram_admin module")
        except (ImportError, AttributeError) as e:
            self.fail(f"Failed to import telegram_admin module or access ADMIN_ID: {e}")

if __name__ == '__main__':
    unittest.main()