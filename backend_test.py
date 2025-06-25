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

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

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

if __name__ == '__main__':
    print(f"🚀 Testing API at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)