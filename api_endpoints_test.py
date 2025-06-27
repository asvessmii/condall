import requests
import unittest
import uuid
import json
import sys
import os

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class AirConditionerShopAPIEndpointsTest(unittest.TestCase):
    """Comprehensive test suite for all API endpoints"""

    def setUp(self):
        """Initialize test data"""
        # Generate a unique user_id for this test session
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"\n🔍 Testing with user_id: {self.test_user_id}")
        
    def tearDown(self):
        """Clean up after tests"""
        # Clear cart after tests
        try:
            requests.delete(f"{API_URL}/cart", params={"user_id": self.test_user_id})
            print(f"✅ Cleaned up cart for user: {self.test_user_id}")
        except Exception as e:
            print(f"❌ Error cleaning up cart: {e}")

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200, "Failed to access API root")
        
        data = response.json()
        self.assertIn("message", data, "API root response missing 'message' field")
        print(f"✅ API root endpoint works: {data['message']}")

    def test_02_get_products(self):
        """Test getting all products"""
        print("\n🔍 Testing GET /api/products endpoint...")
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200, "Failed to get products")
        
        products = response.json()
        self.assertIsInstance(products, list, "Products response is not a list")
        self.assertGreater(len(products), 0, "No products returned")
        
        # Store a product for later tests
        self.test_product = products[0]
        print(f"Using test product: {self.test_product['name']} (ID: {self.test_product['id']})")
        
        # Verify product structure
        required_fields = ['id', 'name', 'description', 'short_description', 'price', 'image_url', 'specifications']
        for field in required_fields:
            self.assertIn(field, self.test_product, f"Product missing required field: {field}")
        
        print(f"✅ GET /api/products returned {len(products)} products with valid structure")

    def test_03_get_product_by_id(self):
        """Test getting a specific product by ID"""
        # First get all products to get a valid ID
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test")
        
        product_id = products[0]['id']
        
        print(f"\n🔍 Testing GET /api/products/{product_id}...")
        response = requests.get(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get product with ID {product_id}")
        
        product = response.json()
        self.assertEqual(product['id'], product_id, "Product ID mismatch")
        print(f"✅ Successfully retrieved product: {product['name']}")

    def test_04_get_empty_cart(self):
        """Test getting an empty cart"""
        print(f"\n🔍 Testing GET /api/cart for new user {self.test_user_id}...")
        response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        self.assertEqual(response.status_code, 200, "Failed to get cart")
        
        cart_items = response.json()
        self.assertIsInstance(cart_items, list, "Cart response is not a list")
        self.assertEqual(len(cart_items), 0, "New user's cart should be empty")
        
        print(f"✅ GET /api/cart returned empty cart for new user {self.test_user_id}")

    def test_05_add_to_cart(self):
        """Test adding a product to the cart"""
        # First get a product to add to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        print(f"\n🔍 Testing POST /api/cart to add product {product['name']}...")
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 2
        }
        
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200, "Failed to add product to cart")
        
        cart_item = response.json()
        self.assertEqual(cart_item['product_id'], product['id'], "Product ID mismatch")
        self.assertEqual(cart_item['quantity'], 2, "Quantity mismatch")
        self.assertEqual(cart_item['user_id'], self.test_user_id, "User ID mismatch")
        
        # Store the cart item ID for later tests
        self.cart_item_id = cart_item['id']
        
        print(f"✅ POST /api/cart successfully added {cart_item['product_name']} x {cart_item['quantity']} to cart")

    def test_06_get_cart_with_items(self):
        """Test getting a cart with items"""
        # First add an item to the cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        
        add_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(add_response.status_code, 200, "Failed to add product to cart")
        
        print(f"\n🔍 Testing GET /api/cart for user {self.test_user_id} with items...")
        response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        self.assertEqual(response.status_code, 200, "Failed to get cart")
        
        cart_items = response.json()
        self.assertIsInstance(cart_items, list, "Cart response is not a list")
        self.assertGreater(len(cart_items), 0, "Cart should have items")
        
        # Verify cart item structure
        cart_item = cart_items[0]
        required_fields = ['id', 'user_id', 'product_id', 'product_name', 'price', 'quantity']
        for field in required_fields:
            self.assertIn(field, cart_item, f"Cart item missing required field: {field}")
        
        print(f"✅ GET /api/cart returned {len(cart_items)} items for user {self.test_user_id}")

    def test_07_update_cart_quantity(self):
        """Test updating quantity by adding the same product again"""
        # First get a product to add to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        # Add product first time
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 2
        }
        
        first_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(first_response.status_code, 200, "Failed to add product to cart first time")
        first_item = first_response.json()
        
        print(f"\n🔍 Testing updating cart quantity by adding same product again...")
        
        # Add same product second time
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 3
        }
        
        second_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(second_response.status_code, 200, "Failed to add product to cart second time")
        second_item = second_response.json()
        
        # Verify quantity was updated, not duplicated
        self.assertEqual(first_item['id'], second_item['id'], "Cart item IDs should be the same")
        self.assertEqual(second_item['quantity'], 5, "Quantity should be sum of both additions (2+3=5)")
        
        # Check cart to confirm only one item
        response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = response.json()
        self.assertEqual(len(cart_items), 1, "Cart should have only one item with updated quantity")
        
        print(f"✅ Successfully updated cart quantity to {second_item['quantity']}")

    def test_08_remove_from_cart(self):
        """Test removing an item from the cart"""
        # First add an item to the cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        
        add_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(add_response.status_code, 200, "Failed to add product to cart")
        cart_item = add_response.json()
        
        print(f"\n🔍 Testing DELETE /api/cart/{cart_item['id']} to remove item...")
        response = requests.delete(f"{API_URL}/cart/{cart_item['id']}", params={"user_id": self.test_user_id})
        self.assertEqual(response.status_code, 200, "Failed to remove item from cart")
        
        # Verify cart is empty
        get_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = get_response.json()
        self.assertEqual(len(cart_items), 0, "Cart should be empty after removing item")
        
        print(f"✅ DELETE /api/cart/{cart_item['id']} successfully removed item from cart")

    def test_09_clear_cart(self):
        """Test clearing the entire cart"""
        # First add an item to the cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 1
        }
        
        add_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(add_response.status_code, 200, "Failed to add product to cart")
        
        # Verify cart has items
        check_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        self.assertGreater(len(check_response.json()), 0, "Cart should have items before clearing")
        
        print(f"\n🔍 Testing DELETE /api/cart to clear entire cart...")
        response = requests.delete(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        self.assertEqual(response.status_code, 200, "Failed to clear cart")
        
        # Verify cart is empty
        get_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = get_response.json()
        self.assertEqual(len(cart_items), 0, "Cart should be empty after clearing")
        
        print(f"✅ DELETE /api/cart successfully cleared entire cart")

    def test_10_cart_isolation(self):
        """Test that carts are isolated between users"""
        print(f"\n🔍 Testing cart isolation between users...")
        
        # Create a second test user
        second_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Get a product to add to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test cart")
        
        product = products[0]
        
        # Add item to first user's cart
        requests.post(f"{API_URL}/cart", json={
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 3
        })
        
        # Add different quantity to second user's cart
        requests.post(f"{API_URL}/cart", json={
            "user_id": second_user_id,
            "product_id": product['id'],
            "quantity": 1
        })
        
        # Get first user's cart
        first_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        first_cart = first_response.json()
        
        # Get second user's cart
        second_response = requests.get(f"{API_URL}/cart", params={"user_id": second_user_id})
        second_cart = second_response.json()
        
        # Verify carts are different
        self.assertNotEqual(len(first_cart), 0, "First user's cart should not be empty")
        self.assertNotEqual(len(second_cart), 0, "Second user's cart should not be empty")
        
        # Same product, different quantity case
        first_quantity = first_cart[0]['quantity']
        second_quantity = second_cart[0]['quantity']
        self.assertNotEqual(first_quantity, second_quantity, "Users should have different quantities in cart")
        
        # Try to delete second user's item with first user's credentials
        if len(second_cart) > 0:
            second_item_id = second_cart[0]['id']
            cross_delete_response = requests.delete(
                f"{API_URL}/cart/{second_item_id}", 
                params={"user_id": self.test_user_id}
            )
            self.assertEqual(cross_delete_response.status_code, 404, 
                            "Should not be able to delete another user's cart item")
        
        # Clean up second user's cart
        requests.delete(f"{API_URL}/cart", params={"user_id": second_user_id})
        
        print(f"✅ Cart isolation between users works correctly")

    def test_11_submit_feedback(self):
        """Test submitting feedback"""
        print("\n🔍 Testing POST /api/feedback...")
        
        feedback_data = {
            "name": "Тестовый Пользователь",
            "phone": "+7 (999) 123-45-67",
            "message": "Это тестовое сообщение для проверки формы обратной связи.",
            "tg_user_id": self.test_user_id,
            "tg_username": "test_username"
        }
        
        response = requests.post(f"{API_URL}/feedback", json=feedback_data)
        self.assertEqual(response.status_code, 200, "Failed to submit feedback")
        
        data = response.json()
        self.assertIn("message", data, "Feedback response missing 'message' field")
        print(f"✅ Feedback submitted successfully: {data['message']}")

    def test_12_create_order(self):
        """Test creating an order"""
        # First add items to cart
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        if not products:
            self.fail("No products available to test order")
        
        product = products[0]
        
        # Add to cart
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": product['id'],
            "quantity": 2
        }
        
        add_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(add_response.status_code, 200, "Failed to add product to cart")
        
        # Get cart
        get_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = get_response.json()
        self.assertGreater(len(cart_items), 0, "Cart should have items before creating order")
        
        print("\n🔍 Testing POST /api/orders...")
        
        # Create order
        order_data = {
            "items": cart_items,
            "tg_user_id": self.test_user_id,
            "tg_username": "test_username"
        }
        
        response = requests.post(f"{API_URL}/orders", json=order_data)
        self.assertEqual(response.status_code, 200, "Failed to create order")
        
        data = response.json()
        self.assertIn("message", data, "Order response missing 'message' field")
        print(f"✅ Order created successfully: {data['message']}")
        
        # Verify cart is cleared after order
        get_response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = get_response.json()
        self.assertEqual(len(cart_items), 0, "Cart should be empty after creating order")
        print("✅ Cart is cleared after order creation")

    def test_13_get_projects(self):
        """Test getting all projects"""
        print("\n🔍 Testing GET /api/projects endpoint...")
        response = requests.get(f"{API_URL}/projects")
        self.assertEqual(response.status_code, 200, "Failed to get projects")
        
        projects = response.json()
        self.assertIsInstance(projects, list, "Projects response is not a list")
        self.assertGreater(len(projects), 0, "No projects returned")
        
        # Verify project structure
        project = projects[0]
        required_fields = ['id', 'title', 'description', 'address', 'images']
        for field in required_fields:
            self.assertIn(field, project, f"Project missing required field: {field}")
        
        print(f"✅ GET /api/projects returned {len(projects)} projects with valid structure")

if __name__ == '__main__':
    print(f"🚀 Testing API Endpoints at: {API_URL}")
    
    # Create a test suite with individual tests
    suite = unittest.TestSuite()
    
    # Add tests one by one
    test_cases = [
        AirConditionerShopAPIEndpointsTest('test_01_api_root'),
        AirConditionerShopAPIEndpointsTest('test_02_get_products'),
        AirConditionerShopAPIEndpointsTest('test_03_get_product_by_id'),
        AirConditionerShopAPIEndpointsTest('test_04_get_empty_cart'),
        AirConditionerShopAPIEndpointsTest('test_05_add_to_cart'),
        AirConditionerShopAPIEndpointsTest('test_06_get_cart_with_items'),
        AirConditionerShopAPIEndpointsTest('test_07_update_cart_quantity'),
        AirConditionerShopAPIEndpointsTest('test_08_remove_from_cart'),
        AirConditionerShopAPIEndpointsTest('test_09_clear_cart'),
        AirConditionerShopAPIEndpointsTest('test_10_cart_isolation'),
        AirConditionerShopAPIEndpointsTest('test_11_submit_feedback'),
        AirConditionerShopAPIEndpointsTest('test_12_create_order'),
        AirConditionerShopAPIEndpointsTest('test_13_get_projects')
    ]
    
    # Run tests one by one with detailed output
    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"RUNNING TEST: {test_case._testMethodName}")
        print(f"{'='*80}")
        result = unittest.TextTestRunner(verbosity=2).run(test_case)
        if not result.wasSuccessful():
            print(f"❌ Test {test_case._testMethodName} FAILED!")
            break
        else:
            print(f"✅ Test {test_case._testMethodName} PASSED!")