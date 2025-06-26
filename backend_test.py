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
        
        # 1. Add to cart
        print(f"\n🔍 Testing add to cart: {product['name']}...")
        cart_data = {
            "product_id": product['id'],
            "quantity": 2
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200)
        cart_item = response.json()
        self.assertEqual(cart_item['product_id'], product['id'])
        self.assertEqual(cart_item['quantity'], 2)
        print(f"✅ Added to cart: {cart_item['product_name']} x {cart_item['quantity']}")
        
        # 2. Get cart
        print("\n🔍 Testing get cart...")
        response = requests.get(f"{API_URL}/cart")
        self.assertEqual(response.status_code, 200)
        cart_items = response.json()
        self.assertIsInstance(cart_items, list)
        self.assertGreater(len(cart_items), 0)
        print(f"✅ Cart contains {len(cart_items)} items")
        
        # 3. Remove from cart
        item_id = cart_items[0]['id']
        print(f"\n🔍 Testing remove from cart: {item_id}...")
        response = requests.delete(f"{API_URL}/cart/{item_id}")
        self.assertEqual(response.status_code, 200)
        print("✅ Item removed from cart")
        
        # 4. Verify cart is empty
        response = requests.get(f"{API_URL}/cart")
        cart_items = response.json()
        self.assertEqual(len(cart_items), 0)
        print("✅ Cart is empty after removal")

    def test_06_feedback_submission(self):
        """Test feedback form submission"""
        print("\n🔍 Testing feedback submission...")
        feedback_data = {
            "name": "Тестовый Пользователь",
            "phone": "+7 (999) 123-45-67",
            "message": "Это тестовое сообщение для проверки формы обратной связи."
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Feedback submitted successfully: {data['message']}")

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

    def test_08_order_creation(self):
        """Test order creation"""
        # First add items to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test order")
        
        product = products[0]
        
        # Add to cart
        cart_data = {
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        cart_item = response.json()
        
        # Get cart
        response = requests.get(f"{API_URL}/cart")
        cart_items = response.json()
        
        # Create order
        print("\n🔍 Testing order creation...")
        order_data = {
            "items": cart_items
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Order created successfully: {data['message']}")
        
        # Verify cart is cleared after order
        response = requests.get(f"{API_URL}/cart")
        cart_items = response.json()
        self.assertEqual(len(cart_items), 0)
        print("✅ Cart is cleared after order creation")

class TelegramBotAdminPanelTest(unittest.TestCase):
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
        self.assertEqual(len(keyboard.inline_keyboard), 3)
        self.assertEqual(keyboard.inline_keyboard[0][0].text, "📦 Управление товарами")
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "manage_products")
        self.assertEqual(keyboard.inline_keyboard[1][0].text, "🏗️ Управление проектами")
        self.assertEqual(keyboard.inline_keyboard[1][0].callback_data, "manage_projects")
        self.assertEqual(keyboard.inline_keyboard[2][0].text, "📊 Статистика")
        self.assertEqual(keyboard.inline_keyboard[2][0].callback_data, "statistics")
        
        print("✅ Main menu keyboard is correctly structured")

    @patch('telegram_admin.check_admin')
    async def test_04_start_command(self, mock_check_admin):
        """Test start command handler"""
        print("\n🔍 Testing start command handler...")
        
        # Mock check_admin to return True
        mock_check_admin.return_value = True
        
        # Call start_command
        await self.telegram_admin.start_command(self.mock_update, self.mock_context)
        
        # Check if welcome message was sent
        self.mock_message.reply_text.assert_called()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Админ панель КЛИМАТ ТЕХНО", call_args)
        
        print("✅ Start command sends welcome message with main menu")

    @patch('telegram_admin.check_admin_callback')
    async def test_05_button_handler_main_menu(self, mock_check_admin_callback):
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
    async def test_06_button_handler_manage_products(self, mock_check_admin_callback):
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
    async def test_07_button_handler_manage_projects(self, mock_check_admin_callback):
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

    @patch('telegram_admin.check_admin_callback')
    async def test_08_add_product_flow_start(self, mock_check_admin_callback):
        """Test starting add product flow"""
        print("\n🔍 Testing add product flow initialization...")
        
        # Mock check_admin_callback to return True
        mock_check_admin_callback.return_value = True
        
        # Set up callback query data
        self.mock_query.data = "add_product"
        
        # Call button_handler
        await self.telegram_admin.button_handler(self.mock_update, self.mock_context)
        
        # Check if add product prompt was displayed
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("Добавление нового товара", call_args)
        self.assertIn("Введите название товара", call_args)
        
        # Check if state was updated
        user_id = self.admin_user.id
        self.assertEqual(self.telegram_admin.admin_state.get_action(user_id), "add_product_name")
        
        print("✅ Add product flow correctly initialized")

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

    def test_17_dependencies_installed(self):
        """Test that required dependencies are installed"""
        print("\n🔍 Testing required dependencies...")
        
        # Check for python-telegram-bot
        try:
            import telegram
            print(f"✅ python-telegram-bot is installed")
        except ImportError:
            self.fail("python-telegram-bot is not installed")
        
        # Check for Pillow
        try:
            import PIL
            print(f"✅ Pillow is installed")
        except ImportError:
            self.fail("Pillow is not installed")
        
        # Check for motor (MongoDB driver)
        try:
            import motor
            print(f"✅ motor is installed")
        except ImportError:
            self.fail("motor is not installed")

if __name__ == '__main__':
    print(f"🚀 Testing API at: {API_URL}")
    print(f"🚀 Testing Telegram Bot Admin Panel")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)