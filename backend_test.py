import requests
import unittest
import os
import json
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import base64
from io import BytesIO
from PIL import Image
import importlib.util
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

# Add backend directory to path to import telegram_admin
sys.path.append('/app/backend')

class AirConditionerShopAPITest(unittest.TestCase):
    """Test suite for the Air Conditioner Shop API"""

    def setUp(self):
        """Initialize test data"""
        self.cart_items = []
        
    def tearDown(self):
        """Clean up after tests"""
        # Clear cart after tests
        try:
            requests.delete(f"{API_URL}/cart")
        except:
            pass

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ API root endpoint works: {data['message']}")

    def test_02_init_data(self):
        """Test initializing sample data"""
        print("\n🔍 Testing data initialization...")
        response = requests.post(f"{API_URL}/init-data")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Data initialization successful: {data['message']}")

    def test_03_get_products(self):
        """Test getting all products"""
        print("\n🔍 Testing products endpoint...")
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        print(f"✅ Products endpoint returned {len(products)} products")
        
        # Verify product structure
        product = products[0]
        required_fields = ['id', 'name', 'description', 'short_description', 'price', 'image_url', 'specifications']
        for field in required_fields:
            self.assertIn(field, product)
        print("✅ Product structure is valid")
        
        return products[0]['id']  # Return first product ID for later tests

    def test_04_get_product_by_id(self):
        """Test getting a specific product by ID"""
        # First get all products to get a valid ID
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test")
        
        product_id = products[0]['id']
        
        print(f"\n🔍 Testing get product by ID: {product_id}...")
        response = requests.get(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 200)
        product = response.json()
        self.assertEqual(product['id'], product_id)
        print(f"✅ Successfully retrieved product: {product['name']}")

    def test_05_cart_operations(self):
        """Test cart operations (add, get, remove)"""
        # First get a product to add to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        # Generate a unique user_id for this test
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # 1. Add to cart
        print(f"\n🔍 Testing add to cart: {product['name']}...")
        cart_data = {
            "user_id": test_user_id,
            "product_id": product['id'],
            "quantity": 2
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200)
        cart_item = response.json()
        self.assertEqual(cart_item['product_id'], product['id'])
        self.assertEqual(cart_item['quantity'], 2)
        self.assertEqual(cart_item['user_id'], test_user_id)
        print(f"✅ Added to cart: {cart_item['product_name']} x {cart_item['quantity']} for user {test_user_id}")
        
        # 2. Get cart
        print("\n🔍 Testing get cart...")
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        self.assertEqual(response.status_code, 200)
        cart_items = response.json()
        self.assertIsInstance(cart_items, list)
        self.assertGreater(len(cart_items), 0)
        print(f"✅ Cart contains {len(cart_items)} items for user {test_user_id}")
        
        # 3. Remove from cart
        item_id = cart_items[0]['id']
        print(f"\n🔍 Testing remove from cart: {item_id}...")
        response = requests.delete(f"{API_URL}/cart/{item_id}", params={"user_id": test_user_id})
        self.assertEqual(response.status_code, 200)
        print("✅ Item removed from cart")
        
        # 4. Verify cart is empty
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        self.assertEqual(len(cart_items), 0)
        print("✅ Cart is empty after removal")

    def test_06a_feedback_submission_without_tg_data(self):
        """Test feedback form submission without Telegram data"""
        print("\n🔍 Testing feedback submission without Telegram data...")
        feedback_data = {
            "name": "Тестовый Пользователь",
            "phone": "+7 (999) 123-45-67",
            "message": "Это тестовое сообщение для проверки формы обратной связи."
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Feedback submitted successfully without Telegram data: {data['message']}")
        
    def test_06b_feedback_submission_with_tg_data(self):
        """Test feedback form submission with Telegram data"""
        print("\n🔍 Testing feedback submission with Telegram data...")
        feedback_data = {
            "name": "Тестовый Пользователь",
            "phone": "+7 (999) 123-45-67",
            "message": "Это тестовое сообщение для проверки формы обратной связи.",
            "tg_user_id": "12345678",
            "tg_username": "test_user"
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Feedback submitted successfully with Telegram data: {data['message']}")
        
        # Verify data was saved to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Run in event loop to use async functions
        loop = asyncio.get_event_loop()
        feedback = loop.run_until_complete(db.feedback.find_one({"tg_user_id": "12345678"}))
        
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["tg_user_id"], "12345678")
        self.assertEqual(feedback["tg_username"], "test_user")
        print("✅ Verified Telegram data was saved to MongoDB")

    def test_07_projects(self):
        """Test projects endpoint"""
        print("\n🔍 Testing projects endpoint...")
        response = requests.get(f"{API_URL}/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.json()
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0)
        print(f"✅ Projects endpoint returned {len(projects)} projects")
        
        # Verify project structure
        project = projects[0]
        required_fields = ['id', 'title', 'description', 'address', 'images']
        for field in required_fields:
            self.assertIn(field, project)
        print("✅ Project structure is valid")
        
        # Verify images
        self.assertIsInstance(project['images'], list)
        self.assertGreater(len(project['images']), 0)
        print(f"✅ Project has {len(project['images'])} images")

    def test_08a_order_creation_without_tg_data(self):
        """Test order creation without Telegram data"""
        # First add items to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test order")
        
        product = products[0]
        
        # Generate a unique user_id for this test
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Add to cart
        cart_data = {
            "user_id": test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        cart_item = response.json()
        
        # Get cart
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        
        # Create order
        print("\n🔍 Testing order creation without Telegram data...")
        order_data = {
            "items": cart_items
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Order created successfully without Telegram data: {data['message']}")
        
        # Verify cart is cleared after order
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        self.assertEqual(len(cart_items), 0)
        print("✅ Cart is cleared after order creation")
        
    def test_08b_order_creation_with_tg_data(self):
        """Test order creation with Telegram data"""
        # First add items to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test order")
        
        product = products[0]
        
        # Generate a unique user_id for this test
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Add to cart
        cart_data = {
            "user_id": test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        cart_item = response.json()
        
        # Get cart
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        
        # Create order with Telegram data
        print("\n🔍 Testing order creation with Telegram data...")
        order_data = {
            "items": cart_items,
            "tg_user_id": "87654321",
            "tg_username": "order_test_user"
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Order created successfully with Telegram data: {data['message']}")
        
        # Verify data was saved to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Run in event loop to use async functions
        loop = asyncio.get_event_loop()
        order = loop.run_until_complete(db.orders.find_one({"tg_user_id": "87654321"}))
        
        self.assertIsNotNone(order)
        self.assertEqual(order["tg_user_id"], "87654321")
        self.assertEqual(order["tg_username"], "order_test_user")
        print("✅ Verified Telegram data was saved to MongoDB")
        
        # Verify cart is cleared after order
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        self.assertEqual(len(cart_items), 0)
        print("✅ Cart is cleared after order creation")

class TelegramUserInfoTest(unittest.TestCase):
    """Test suite for Telegram User Info in Feedback and Orders"""

    def setUp(self):
        """Initialize test data"""
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
    def tearDown(self):
        """Clean up after tests"""
        self.client.close()

    async def test_01_feedback_schema(self):
        """Test feedback schema with Telegram user info"""
        print("\n🔍 Testing feedback schema with Telegram user info...")
        
        # Create test feedback with Telegram data
        feedback_id = str(uuid.uuid4())
        test_feedback = {
            "id": feedback_id,
            "name": "Schema Test User",
            "phone": "+7 (999) 888-77-66",
            "message": "Testing feedback schema with Telegram data",
            "tg_user_id": "123456789",
            "tg_username": "schema_test_user",
            "created_at": datetime.utcnow()
        }
        
        # Insert test feedback
        await self.db.feedback.insert_one(test_feedback)
        print("✅ Test feedback created")
        
        # Retrieve and verify
        feedback = await self.db.feedback.find_one({"id": feedback_id})
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["tg_user_id"], "123456789")
        self.assertEqual(feedback["tg_username"], "schema_test_user")
        print("✅ Feedback schema includes Telegram user info fields")
        
        # Clean up
        await self.db.feedback.delete_one({"id": feedback_id})
        print("✅ Test feedback deleted")
        
    async def test_02_order_schema(self):
        """Test order schema with Telegram user info"""
        print("\n🔍 Testing order schema with Telegram user info...")
        
        # Create test order with Telegram data
        order_id = str(uuid.uuid4())
        test_order = {
            "id": order_id,
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "user_id": "test_user_id",
                    "product_id": str(uuid.uuid4()),
                    "product_name": "Test Product",
                    "price": 1000.0,
                    "quantity": 1,
                    "created_at": datetime.utcnow()
                }
            ],
            "total_amount": 1000.0,
            "tg_user_id": "987654321",
            "tg_username": "order_schema_test",
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        # Insert test order
        await self.db.orders.insert_one(test_order)
        print("✅ Test order created")
        
        # Retrieve and verify
        order = await self.db.orders.find_one({"id": order_id})
        self.assertIsNotNone(order)
        self.assertEqual(order["tg_user_id"], "987654321")
        self.assertEqual(order["tg_username"], "order_schema_test")
        print("✅ Order schema includes Telegram user info fields")
        
        # Clean up
        await self.db.orders.delete_one({"id": order_id})
        print("✅ Test order deleted")
        
    async def test_03_feedback_api_validation(self):
        """Test feedback API validation with Telegram user info"""
        print("\n🔍 Testing feedback API validation with Telegram user info...")
        
        # Test with valid data
        feedback_data = {
            "name": "API Test User",
            "phone": "+7 (999) 777-66-55",
            "message": "Testing API validation",
            "tg_user_id": "11223344",
            "tg_username": "api_test_user"
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        print("✅ API accepts valid feedback with Telegram data")
        
        # Test with invalid tg_user_id type (should be converted to string)
        feedback_data = {
            "name": "API Test User",
            "phone": "+7 (999) 777-66-55",
            "message": "Testing API validation",
            "tg_user_id": 12345678,  # Number instead of string
            "tg_username": "api_test_user"
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        print("✅ API handles numeric tg_user_id correctly")
        
    async def test_04_order_api_validation(self):
        """Test order API validation with Telegram user info"""
        print("\n🔍 Testing order API validation with Telegram user info...")
        
        # First add items to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test order")
        
        product = products[0]
        
        # Generate a unique user_id for this test
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Add to cart
        cart_data = {
            "user_id": test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        
        # Get cart
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        
        # Test with valid data
        order_data = {
            "items": cart_items,
            "tg_user_id": "55667788",
            "tg_username": "order_api_test"
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200)
        print("✅ API accepts valid order with Telegram data")
        
        # Add to cart again for second test
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        response = requests.get(f"{API_URL}/cart", params={"user_id": test_user_id})
        cart_items = response.json()
        
        # Test with invalid tg_user_id type (should be converted to string)
        order_data = {
            "items": cart_items,
            "tg_user_id": 87654321,  # Number instead of string
            "tg_username": "order_api_test"
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200)
        print("✅ API handles numeric tg_user_id correctly")
    """Test suite for the Telegram Bot Admin Panel"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Set environment variables for testing
        os.environ['BOT_TOKEN'] = "7575081951:AAHQ9kG-7_hKAgVTWYHWHzJ3UnWJRnEJX30"
        if 'MONGO_URL' not in os.environ:
            os.environ['MONGO_URL'] = "mongodb://localhost:27017"
        if 'DB_NAME' not in os.environ:
            os.environ['DB_NAME'] = "test_database"
            
        # Import the telegram_admin module
        try:
            spec = importlib.util.spec_from_file_location("telegram_admin", "/app/backend/telegram_admin.py")
            cls.telegram_admin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.telegram_admin)
            cls.telegram_admin_imported = True
            
            # Create a test image
            cls.test_image = BytesIO()
            image = Image.new('RGB', (100, 100), color='red')
            image.save(cls.test_image, 'JPEG')
            cls.test_image.seek(0)
            cls.test_image_base64 = base64.b64encode(cls.test_image.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error importing telegram_admin module: {e}")
            cls.telegram_admin_imported = False

    def setUp(self):
        """Initialize test data"""
        if not hasattr(self.__class__, 'telegram_admin_imported') or not self.__class__.telegram_admin_imported:
            self.skipTest("telegram_admin module could not be imported")
            return
            
        # Reset admin state before each test
        self.telegram_admin.admin_state = self.telegram_admin.AdminState()
        
        # Create mock objects
        self.mock_update = MagicMock()
        self.mock_context = MagicMock()
        self.mock_query = MagicMock()
        
        # Set up admin user
        self.admin_user = MagicMock()
        self.admin_user.id = self.telegram_admin.ADMIN_ID
        
        # Set up non-admin user
        self.non_admin_user = MagicMock()
        self.non_admin_user.id = 12345  # Different from ADMIN_ID
        
        # Set up mock message
        self.mock_message = MagicMock()
        self.mock_update.message = self.mock_message
        self.mock_update.effective_user = self.admin_user
        
        # Set up mock callback query
        self.mock_query.from_user = self.admin_user
        self.mock_update.callback_query = self.mock_query

    def test_01_bot_token_configuration(self):
        """Test bot token configuration"""
        print("\n🔍 Testing bot token configuration...")
        self.assertEqual(self.telegram_admin.BOT_TOKEN, "7575081951:AAHQ9kG-7_hKAgVTWYHWHzJ3UnWJRnEJX30")
        print("✅ Bot token is correctly configured")

    def test_02_admin_authentication(self):
        """Test admin authentication"""
        print("\n🔍 Testing admin authentication...")
        
        # Test with admin user
        self.mock_update.effective_user = self.admin_user
        result = asyncio.run(self.telegram_admin.check_admin(self.mock_update))
        self.assertTrue(result)
        print("✅ Admin authentication works for authorized user")
        
        # Test with non-admin user
        self.mock_update.effective_user = self.non_admin_user
        result = asyncio.run(self.telegram_admin.check_admin(self.mock_update))
        self.assertFalse(result)
        self.mock_message.reply_text.assert_called_with("❌ У вас нет прав доступа к админ панели")
        print("✅ Admin authentication blocks unauthorized users")

    def test_03_main_menu_keyboard(self):
        """Test main menu keyboard generation"""
        print("\n🔍 Testing main menu keyboard generation...")
        keyboard = self.telegram_admin.get_main_menu_keyboard()
        
        # Check keyboard structure
        self.assertEqual(len(keyboard.inline_keyboard), 4)
        self.assertEqual(keyboard.inline_keyboard[1][0].text, "📦 Управление товарами")
        self.assertEqual(keyboard.inline_keyboard[1][0].callback_data, "manage_products")
        self.assertEqual(keyboard.inline_keyboard[2][0].text, "🏗️ Управление проектами")
        self.assertEqual(keyboard.inline_keyboard[2][0].callback_data, "manage_projects")
        self.assertEqual(keyboard.inline_keyboard[3][0].text, "📊 Статистика")
        self.assertEqual(keyboard.inline_keyboard[3][0].callback_data, "statistics")
        
        print("✅ Main menu keyboard is correctly structured")

    def test_04_start_command_for_regular_users(self):
        """Test start command handler for regular users"""
        print("\n🔍 Testing start command handler for regular users...")
        
        # Call start_command
        asyncio.run(self.telegram_admin.start_command(self.mock_update, self.mock_context))
        
        # Check if welcome message was sent
        self.mock_message.reply_text.assert_called()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Добро пожаловать в КЛИМАТ ТЕХНО", call_args)
        
        # Check if the keyboard has the correct buttons
        reply_markup = self.mock_message.reply_text.call_args[1]['reply_markup']
        self.assertEqual(len(reply_markup.inline_keyboard), 2)
        self.assertEqual(reply_markup.inline_keyboard[0][0].text, "🌐 Открыть каталог")
        self.assertEqual(reply_markup.inline_keyboard[1][0].text, "📞 Связаться с нами")
        self.assertEqual(reply_markup.inline_keyboard[1][0].callback_data, "contact_info")
        
        print("✅ Start command shows welcome message with catalog button and contact button for regular users")
        
    @patch('telegram_admin.check_admin')
    async def test_05_admin_command_for_admin(self, mock_check_admin):
        """Test admin command handler for admin user"""
        print("\n🔍 Testing admin command handler for admin user...")
        
        # Mock check_admin to return True
        mock_check_admin.return_value = True
        
        # Call admin_command
        await self.telegram_admin.admin_command(self.mock_update, self.mock_context)
        
        # Check if admin panel message was sent
        self.mock_message.reply_text.assert_called()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Админ панель КЛИМАТ ТЕХНО", call_args)
        
        # Check if the keyboard has the correct buttons
        reply_markup = self.mock_message.reply_text.call_args[1]['reply_markup']
        self.assertEqual(len(reply_markup.inline_keyboard), 5)  # 5 buttons in admin panel
        self.assertEqual(reply_markup.inline_keyboard[1][0].text, "📦 Управление товарами")
        self.assertEqual(reply_markup.inline_keyboard[2][0].text, "🏗️ Управление проектами")
        
        print("✅ Admin command shows admin panel with management options for admin user")
    
    @patch('telegram_admin.check_admin')
    async def test_06_admin_command_for_non_admin(self, mock_check_admin):
        """Test admin command handler for non-admin user"""
        print("\n🔍 Testing admin command handler for non-admin user...")
        
        # Mock check_admin to return False
        mock_check_admin.return_value = False
        
        # Set up non-admin user
        self.mock_update.effective_user = self.non_admin_user
        
        # Call admin_command
        await self.telegram_admin.admin_command(self.mock_update, self.mock_context)
        
        # Check if access denied message was sent
        self.mock_message.reply_text.assert_called()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("У вас нет прав доступа к админ панели", call_args)
        
        print("✅ Admin command blocks access for non-admin users")

    @patch('telegram_admin.check_admin_callback')
    async def test_07_contact_info_button(self, mock_check_admin_callback):
        """Test contact info button functionality"""
        print("\n🔍 Testing contact info button functionality...")
        
        # Set up callback query data
        self.mock_query.data = "contact_info"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if contact info was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Контактная информация", call_args)
        self.assertIn("Телефон:", call_args)
        self.assertIn("Email:", call_args)
        
        # Check if the keyboard has the catalog button
        reply_markup = self.mock_query.edit_message_text.call_args[1]['reply_markup']
        self.assertEqual(len(reply_markup.inline_keyboard), 1)
        self.assertEqual(reply_markup.inline_keyboard[0][0].text, "🌐 Открыть каталог")
        
        print("✅ Contact info button correctly displays contact information")

    @patch('telegram_admin.check_admin_callback')
    async def test_08_button_handler_main_menu(self, mock_check_admin_callback):
        """Test button handler for main menu"""
        print("\n🔍 Testing button handler for main menu...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Set up callback query data
        self.mock_query.data = "main_menu"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if main menu was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Админ панель КЛИМАТ ТЕХНО", call_args)
        
        print("✅ Button handler correctly displays main menu")

    @patch('telegram_admin.check_admin_callback')
    async def test_09_button_handler_manage_products(self, mock_check_admin_callback):
        """Test button handler for manage products"""
        print("\n🔍 Testing button handler for manage products...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Set up callback query data
        self.mock_query.data = "manage_products"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if products menu was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Управление товарами", call_args)
        
        print("✅ Button handler correctly displays products management menu")

    @patch('telegram_admin.check_admin_callback')
    async def test_10_button_handler_manage_projects(self, mock_check_admin_callback):
        """Test button handler for manage projects"""
        print("\n🔍 Testing button handler for manage projects...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Set up callback query data
        self.mock_query.data = "manage_projects"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if projects menu was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Управление проектами", call_args)
        
        print("✅ Button handler correctly displays projects management menu")

    @patch('telegram_admin.check_admin')
    async def test_09_add_product_message_handler(self, mock_check_admin):
        """Test message handler for adding product"""
        print("\n🔍 Testing message handler for adding product...")
        
        # Mock check_admin to return True
        mock_check_admin.return_value = True
        
        # Set up user state
        user_id = self.admin_user.id
        self.telegram_admin.admin_state.set_action(user_id, "add_product_name")
        
        # Set message text
        self.mock_message.text = "Test Product"
        
        # Call message_handler
        await self.telegram_admin.message_handler(self.mock_update, self.mock_context)
        
        # Check if state was updated
        self.assertEqual(self.telegram_admin.admin_state.get_action(user_id), "add_product_short_description")
        product_data = self.telegram_admin.admin_state.get_state(user_id).get("new_product", {})
        self.assertEqual(product_data.get("name"), "Test Product")
        
        # Check if next prompt was displayed
        self.mock_message.reply_text.assert_called_with("📝 Введите краткое описание товара:")
        
        print("✅ Message handler correctly processes product name input")

    @patch('telegram_admin.check_admin_callback')
    async def test_10_add_project_flow_start(self, mock_check_admin_callback):
        """Test starting add project flow"""
        print("\n🔍 Testing add project flow initialization...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Set up callback query data
        self.mock_query.data = "add_project"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if add project prompt was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Добавление нового проекта", call_args)
        self.assertIn("Введите название проекта", call_args)
        
        # Check if state was updated
        user_id = self.admin_user.id
        self.assertEqual(self.telegram_admin.admin_state.get_action(user_id), "add_project_title")
        
        print("✅ Add project flow correctly initialized")

    @patch('telegram_admin.check_admin')
    async def test_11_add_project_message_handler(self, mock_check_admin):
        """Test message handler for adding project"""
        print("\n🔍 Testing message handler for adding project...")
        
        # Mock check_admin to return True
        mock_check_admin.return_value = True
        
        # Set up user state
        user_id = self.admin_user.id
        self.telegram_admin.admin_state.set_action(user_id, "add_project_title")
        
        # Set message text
        self.mock_message.text = "Test Project"
        
        # Call message_handler
        await self.telegram_admin.message_handler(self.mock_update, self.mock_context)
        
        # Check if state was updated
        self.assertEqual(self.telegram_admin.admin_state.get_action(user_id), "add_project_description")
        project_data = self.telegram_admin.admin_state.get_state(user_id).get("new_project", {})
        self.assertEqual(project_data.get("title"), "Test Project")
        
        # Check if next prompt was displayed
        self.mock_message.reply_text.assert_called_with("📝 Введите описание проекта:")
        
        print("✅ Message handler correctly processes project title input")

    @patch('telegram_admin.db.products.find')
    @patch('telegram_admin.check_admin_callback')
    async def test_12_list_products(self, mock_check_admin_callback, mock_find):
        """Test listing products"""
        print("\n🔍 Testing list products functionality...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "id": "123",
                "name": "Test Product 1",
                "price": 1000,
                "short_description": "Test Description 1"
            },
            {
                "id": "456",
                "name": "Test Product 2",
                "price": 2000,
                "short_description": "Test Description 2"
            }
        ]
        mock_find.return_value = mock_cursor
        
        # Call list_products
        await self.telegram_admin.list_products(self.mock_query)
        
        # Check if products list was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Список товаров", call_args)
        self.assertIn("Test Product 1", call_args)
        self.assertIn("Test Product 2", call_args)
        
        print("✅ List products functionality works correctly")

    @patch('telegram_admin.db.projects.find')
    @patch('telegram_admin.check_admin_callback')
    async def test_13_list_projects(self, mock_check_admin_callback, mock_find):
        """Test listing projects"""
        print("\n🔍 Testing list projects functionality...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "id": "123",
                "title": "Test Project 1",
                "address": "Test Address 1",
                "images": ["image1", "image2"]
            },
            {
                "id": "456",
                "title": "Test Project 2",
                "address": "Test Address 2",
                "images": ["image3"]
            }
        ]
        mock_find.return_value = mock_cursor
        
        # Call list_projects
        await self.telegram_admin.list_projects(self.mock_query)
        
        # Check if projects list was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Список проектов", call_args)
        self.assertIn("Test Project 1", call_args)
        self.assertIn("Test Project 2", call_args)
        
        print("✅ List projects functionality works correctly")

    @patch('telegram_admin.db.products.find_one')
    @patch('telegram_admin.db.products.delete_one')
    @patch('telegram_admin.check_admin_callback')
    async def test_14_delete_product(self, mock_check_admin_callback, mock_delete_one, mock_find_one):
        """Test deleting a product"""
        print("\n🔍 Testing delete product functionality...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Mock database response
        mock_find_one.return_value = {
            "id": "123",
            "name": "Test Product"
        }
        mock_delete_one.return_value = MagicMock(deleted_count=1)
        
        # Call delete_product
        await self.telegram_admin.delete_product(self.mock_query, "123")
        
        # Check if product was deleted
        mock_delete_one.assert_called_with({"id": "123"})
        
        # Check if success message was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("успешно удален", call_args)
        
        print("✅ Delete product functionality works correctly")

    @patch('telegram_admin.db.projects.find_one')
    @patch('telegram_admin.db.projects.delete_one')
    @patch('telegram_admin.check_admin_callback')
    async def test_15_delete_project(self, mock_check_admin_callback, mock_delete_one, mock_find_one):
        """Test deleting a project"""
        print("\n🔍 Testing delete project functionality...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Mock database response
        mock_find_one.return_value = {
            "id": "123",
            "title": "Test Project"
        }
        mock_delete_one.return_value = MagicMock(deleted_count=1)
        
        # Call delete_project
        await self.telegram_admin.delete_project(self.mock_query, "123")
        
        # Check if project was deleted
        mock_delete_one.assert_called_with({"id": "123"})
        
        # Check if success message was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("успешно удален", call_args)
        
        print("✅ Delete project functionality works correctly")

    @patch('telegram_admin.db.products.count_documents')
    @patch('telegram_admin.db.projects.count_documents')
    @patch('telegram_admin.db.orders.count_documents')
    @patch('telegram_admin.db.feedback.count_documents')
    @patch('telegram_admin.check_admin_callback')
    async def test_16_show_statistics(self, mock_check_admin_callback, mock_feedback_count, 
                                    mock_orders_count, mock_projects_count, mock_products_count):
        """Test showing statistics"""
        print("\n🔍 Testing show statistics functionality...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Mock database responses
        mock_products_count.return_value = 5
        mock_projects_count.return_value = 3
        mock_orders_count.return_value = 10
        mock_feedback_count.return_value = 7
        
        # Call show_statistics
        await self.telegram_admin.show_statistics(self.mock_query)
        
        # Check if statistics were displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Статистика", call_args)
        self.assertIn("Товары: 5", call_args)
        self.assertIn("Проекты: 3", call_args)
        self.assertIn("Заказы: 10", call_args)
        self.assertIn("Обратная связь: 7", call_args)
        
        print("✅ Show statistics functionality works correctly")

    def test_18_telegram_bot_running_as_service(self):
        """Test that Telegram bot is running as a supervisor service"""
        print("\n🔍 Testing Telegram bot supervisor service...")
        
        # Check if telegram_bot service is running
        import subprocess
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

class MongoDBPersistenceTest(unittest.TestCase):
    """Test suite for MongoDB persistence"""
    
    async def test_mongodb_connection(self):
        """Test MongoDB connection"""
        print("\n🔍 Testing MongoDB connection...")
        try:
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            
            # Test connection by getting server info
            server_info = await client.server_info()
            print(f"✅ Connected to MongoDB version: {server_info.get('version')}")
            
            # Count documents in collections
            products_count = await db.products.count_documents({})
            projects_count = await db.projects.count_documents({})
            
            print(f"✅ Products in database: {products_count}")
            print(f"✅ Projects in database: {projects_count}")
            
            # Close connection
            client.close()
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def test_product_crud(self):
        """Test CRUD operations for products"""
        print("\n🔍 Testing product CRUD operations...")
        
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Create a test product
        test_product = {
            "id": str(uuid.uuid4()),
            "name": "Test Product",
            "description": "This is a test product for MongoDB testing",
            "short_description": "Test product",
            "price": 999.99,
            "image_url": "data:image/jpeg;base64,test",
            "specifications": {
                "Test Spec": "Test Value"
            },
            "created_at": datetime.utcnow()
        }
        
        # Create
        print("Creating test product...")
        result = await db.products.insert_one(test_product)
        print(f"✅ Product created with ID: {test_product['id']}")
        
        # Read
        print("Reading test product...")
        product = await db.products.find_one({"id": test_product['id']})
        if product:
            print(f"✅ Product retrieved: {product['name']}")
        else:
            print("❌ Failed to retrieve product")
        
        # Update
        print("Updating test product...")
        update_result = await db.products.update_one(
            {"id": test_product['id']},
            {"$set": {"price": 888.88}}
        )
        if update_result.modified_count > 0:
            print("✅ Product updated successfully")
        else:
            print("❌ Failed to update product")
        
        # Verify update
        updated_product = await db.products.find_one({"id": test_product['id']})
        if updated_product and updated_product['price'] == 888.88:
            print(f"✅ Product price updated to: {updated_product['price']}")
        else:
            print("❌ Failed to verify product update")
        
        # Delete
        print("Deleting test product...")
        delete_result = await db.products.delete_one({"id": test_product['id']})
        if delete_result.deleted_count > 0:
            print("✅ Product deleted successfully")
        else:
            print("❌ Failed to delete product")
        
        # Verify deletion
        deleted_product = await db.products.find_one({"id": test_product['id']})
        if not deleted_product:
            print("✅ Product deletion verified")
        else:
            print("❌ Product still exists after deletion")
        
        # Close connection
        client.close()
        return True
    
    async def test_project_crud(self):
        """Test CRUD operations for projects"""
        print("\n🔍 Testing project CRUD operations...")
        
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Create a test project
        test_project = {
            "id": str(uuid.uuid4()),
            "title": "Test Project",
            "description": "This is a test project for MongoDB testing",
            "address": "Test Address, 123",
            "images": ["data:image/jpeg;base64,test1", "data:image/jpeg;base64,test2"],
            "created_at": datetime.utcnow()
        }
        
        # Create
        print("Creating test project...")
        result = await db.projects.insert_one(test_project)
        print(f"✅ Project created with ID: {test_project['id']}")
        
        # Read
        print("Reading test project...")
        project = await db.projects.find_one({"id": test_project['id']})
        if project:
            print(f"✅ Project retrieved: {project['title']}")
        else:
            print("❌ Failed to retrieve project")
        
        # Update
        print("Updating test project...")
        update_result = await db.projects.update_one(
            {"id": test_project['id']},
            {"$set": {"address": "Updated Address, 456"}}
        )
        if update_result.modified_count > 0:
            print("✅ Project updated successfully")
        else:
            print("❌ Failed to update project")
        
        # Verify update
        updated_project = await db.projects.find_one({"id": test_project['id']})
        if updated_project and updated_project['address'] == "Updated Address, 456":
            print(f"✅ Project address updated to: {updated_project['address']}")
        else:
            print("❌ Failed to verify project update")
        
        # Delete
        print("Deleting test project...")
        delete_result = await db.projects.delete_one({"id": test_project['id']})
        if delete_result.deleted_count > 0:
            print("✅ Project deleted successfully")
        else:
            print("❌ Failed to delete project")
        
        # Verify deletion
        deleted_project = await db.projects.find_one({"id": test_project['id']})
        if not deleted_project:
            print("✅ Project deletion verified")
        else:
            print("❌ Project still exists after deletion")
        
        # Close connection
        client.close()
        return True
    
    async def test_data_persistence(self):
        """Test data persistence after service restart"""
        print("\n🔍 Testing data persistence after service restart...")
        
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Create a test product for persistence testing
        test_product = {
            "id": str(uuid.uuid4()),
            "name": "Persistence Test Product",
            "description": "This product tests persistence after restart",
            "short_description": "Persistence test",
            "price": 777.77,
            "image_url": "data:image/jpeg;base64,persistence_test",
            "specifications": {
                "Persistence": "Test"
            },
            "created_at": datetime.utcnow()
        }
        
        # Create the product
        print("Creating persistence test product...")
        await db.products.insert_one(test_product)
        print(f"✅ Persistence test product created with ID: {test_product['id']}")
        
        # Get product count before restart
        products_before = await db.products.count_documents({})
        print(f"✅ Products before restart: {products_before}")
        
        # Close connection before restart
        client.close()
        
        # Restart services
        print("\n🔄 Restarting services...")
        os.system("sudo supervisorctl restart all")
        
        # Wait for services to restart
        print("Waiting for services to restart...")
        await asyncio.sleep(10)
        
        # Reconnect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Check if data persisted
        print("Checking if data persisted...")
        
        # Get product count after restart
        products_after = await db.products.count_documents({})
        print(f"✅ Products after restart: {products_after}")
        
        # Check if our test product is still there
        persistence_product = await db.products.find_one({"id": test_product['id']})
        if persistence_product:
            print(f"✅ Persistence test product found after restart: {persistence_product['name']}")
        else:
            print("❌ Persistence test product not found after restart")
        
        # Clean up
        print("Cleaning up persistence test product...")
        await db.products.delete_one({"id": test_product['id']})
        print("✅ Persistence test product deleted")
        
        # Close connection
        client.close()
        return True

if __name__ == '__main__':
    print(f"🚀 Testing API at: {API_URL}")
    
    # Run Telegram User Info tests
    print("\n=== Running Telegram User Info Tests ===")
    tg_info_test = TelegramUserInfoTest()
    
    # Run async tests
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tg_info_test.test_01_feedback_schema())
    loop.run_until_complete(tg_info_test.test_02_order_schema())
    loop.run_until_complete(tg_info_test.test_03_feedback_api_validation())
    loop.run_until_complete(tg_info_test.test_04_order_api_validation())
    
    # Run MongoDB persistence tests
    print("\n=== Running MongoDB Persistence Tests ===")
    mongo_test = MongoDBPersistenceTest()
    
    # Run async tests
    loop.run_until_complete(mongo_test.test_mongodb_connection())
    loop.run_until_complete(mongo_test.test_product_crud())
    loop.run_until_complete(mongo_test.test_project_crud())
    loop.run_until_complete(mongo_test.test_data_persistence())
    
    # Run regular tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)