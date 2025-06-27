import requests
import unittest
import uuid
import time
import sys
import os

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class CartFunctionalityTest(unittest.TestCase):
    """Test suite specifically for cart functionality"""

    def setUp(self):
        """Initialize test data"""
        # Generate a unique user_id for this test session
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"\n🔍 Testing with user_id: {self.test_user_id}")
        
        # Get a product to use in tests
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200, "Failed to get products")
        
        products = response.json()
        self.assertGreater(len(products), 0, "No products available for testing")
        
        # Store the first product for testing
        self.test_product = products[0]
        print(f"Using test product: {self.test_product['name']} (ID: {self.test_product['id']})")
        
        # If there's a second product, store it for multi-product tests
        self.second_product = products[1] if len(products) > 1 else None
        
    def tearDown(self):
        """Clean up after tests"""
        # Clear cart after tests
        try:
            requests.delete(f"{API_URL}/cart", params={"user_id": self.test_user_id})
            print(f"✅ Cleaned up cart for user: {self.test_user_id}")
        except Exception as e:
            print(f"❌ Error cleaning up cart: {e}")

    def test_01_get_products(self):
        """Test getting all products"""
        print("\n🔍 Testing GET /api/products endpoint...")
        try:
            response = requests.get(f"{API_URL}/products")
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
            
            self.assertEqual(response.status_code, 200, "Failed to get products")
            
            products = response.json()
            self.assertIsInstance(products, list, "Products response is not a list")
            self.assertGreater(len(products), 0, "No products returned")
            
            # Verify product structure
            product = products[0]
            print(f"First product: {product['name']}")
            required_fields = ['id', 'name', 'description', 'short_description', 'price', 'image_url', 'specifications']
            for field in required_fields:
                self.assertIn(field, product, f"Product missing required field: {field}")
            
            print(f"✅ GET /api/products returned {len(products)} products with valid structure")
        except Exception as e:
            print(f"❌ Error in test_01_get_products: {e}")
            raise

    def test_02_empty_cart(self):
        """Test getting an empty cart"""
        print(f"\n🔍 Testing GET /api/cart for new user {self.test_user_id}...")
        response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        self.assertEqual(response.status_code, 200, "Failed to get cart")
        
        cart_items = response.json()
        self.assertIsInstance(cart_items, list, "Cart response is not a list")
        self.assertEqual(len(cart_items), 0, "New user's cart should be empty")
        
        print(f"✅ GET /api/cart returned empty cart for new user {self.test_user_id}")

    def test_03_add_to_cart(self):
        """Test adding a product to the cart"""
        print(f"\n🔍 Testing POST /api/cart to add product {self.test_product['name']}...")
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
            "quantity": 2
        }
        
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200, "Failed to add product to cart")
        
        cart_item = response.json()
        self.assertEqual(cart_item['product_id'], self.test_product['id'], "Product ID mismatch")
        self.assertEqual(cart_item['quantity'], 2, "Quantity mismatch")
        self.assertEqual(cart_item['user_id'], self.test_user_id, "User ID mismatch")
        self.assertEqual(cart_item['product_name'], self.test_product['name'], "Product name mismatch")
        self.assertEqual(cart_item['price'], self.test_product['price'], "Price mismatch")
        
        # Store the cart item ID for later tests
        self.cart_item_id = cart_item['id']
        
        print(f"✅ POST /api/cart successfully added {cart_item['product_name']} x {cart_item['quantity']} to cart")

    def test_04_get_cart_with_items(self):
        """Test getting a cart with items"""
        # First add an item to the cart
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
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

    def test_05_add_same_product_twice(self):
        """Test adding the same product to the cart twice (should update quantity)"""
        print(f"\n🔍 Testing adding the same product to cart twice...")
        
        # Add product first time
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
            "quantity": 2
        }
        
        first_response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(first_response.status_code, 200, "Failed to add product to cart first time")
        first_item = first_response.json()
        
        # Add same product second time
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
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
        
        print(f"✅ Adding same product twice correctly updated quantity to {second_item['quantity']}")

    def test_06_add_multiple_products(self):
        """Test adding multiple different products to the cart"""
        if not self.second_product:
            self.skipTest("Need at least two products for this test")
            
        print(f"\n🔍 Testing adding multiple products to cart...")
        
        # Add first product
        cart_data_1 = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
            "quantity": 1
        }
        
        response_1 = requests.post(f"{API_URL}/cart", json=cart_data_1)
        self.assertEqual(response_1.status_code, 200, "Failed to add first product to cart")
        
        # Add second product
        cart_data_2 = {
            "user_id": self.test_user_id,
            "product_id": self.second_product['id'],
            "quantity": 2
        }
        
        response_2 = requests.post(f"{API_URL}/cart", json=cart_data_2)
        self.assertEqual(response_2.status_code, 200, "Failed to add second product to cart")
        
        # Check cart to confirm both items
        response = requests.get(f"{API_URL}/cart", params={"user_id": self.test_user_id})
        cart_items = response.json()
        self.assertEqual(len(cart_items), 2, "Cart should have two items")
        
        # Verify both products are in cart
        product_ids = [item['product_id'] for item in cart_items]
        self.assertIn(self.test_product['id'], product_ids, "First product should be in cart")
        self.assertIn(self.second_product['id'], product_ids, "Second product should be in cart")
        
        print(f"✅ Successfully added multiple products to cart")

    def test_07_remove_from_cart(self):
        """Test removing an item from the cart"""
        # First add an item to the cart
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
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

    def test_08_clear_cart(self):
        """Test clearing the entire cart"""
        # Add multiple items to the cart
        if self.second_product:
            # Add two different products
            requests.post(f"{API_URL}/cart", json={
                "user_id": self.test_user_id,
                "product_id": self.test_product['id'],
                "quantity": 1
            })
            
            requests.post(f"{API_URL}/cart", json={
                "user_id": self.test_user_id,
                "product_id": self.second_product['id'],
                "quantity": 2
            })
        else:
            # Add same product twice with different quantities
            requests.post(f"{API_URL}/cart", json={
                "user_id": self.test_user_id,
                "product_id": self.test_product['id'],
                "quantity": 1
            })
            
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

    def test_09_add_nonexistent_product(self):
        """Test adding a non-existent product to the cart"""
        print(f"\n🔍 Testing adding non-existent product to cart...")
        
        # Generate a random product ID that doesn't exist
        fake_product_id = str(uuid.uuid4())
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": fake_product_id,
            "quantity": 1
        }
        
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 404, "Should return 404 for non-existent product")
        
        error_data = response.json()
        self.assertIn("detail", error_data, "Error response should have 'detail' field")
        self.assertEqual(error_data["detail"], "Товар не найден", "Error message should indicate product not found")
        
        print(f"✅ Adding non-existent product correctly returns 404 error")

    def test_10_cart_without_user_id(self):
        """Test cart operations without providing user_id"""
        print(f"\n🔍 Testing cart operations without user_id...")
        
        # Test GET /api/cart without user_id
        get_response = requests.get(f"{API_URL}/cart")
        self.assertEqual(get_response.status_code, 400, "GET /api/cart without user_id should return 400")
        
        # Test POST /api/cart without user_id
        post_data = {
            "product_id": self.test_product['id'],
            "quantity": 1
        }
        post_response = requests.post(f"{API_URL}/cart", json=post_data)
        self.assertEqual(post_response.status_code, 400, "POST /api/cart without user_id should return 400")
        
        # Test DELETE /api/cart without user_id
        delete_response = requests.delete(f"{API_URL}/cart")
        self.assertEqual(delete_response.status_code, 400, "DELETE /api/cart without user_id should return 400")
        
        print(f"✅ All cart operations correctly require user_id parameter")

    def test_11_cart_isolation(self):
        """Test that carts are isolated between users"""
        print(f"\n🔍 Testing cart isolation between users...")
        
        # Create a second test user
        second_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Add item to first user's cart
        requests.post(f"{API_URL}/cart", json={
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
            "quantity": 3
        })
        
        # Add different item or quantity to second user's cart
        if self.second_product:
            # Add different product
            requests.post(f"{API_URL}/cart", json={
                "user_id": second_user_id,
                "product_id": self.second_product['id'],
                "quantity": 1
            })
        else:
            # Add same product with different quantity
            requests.post(f"{API_URL}/cart", json={
                "user_id": second_user_id,
                "product_id": self.test_product['id'],
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
        
        if self.second_product:
            # Different products case
            first_product_id = first_cart[0]['product_id']
            second_product_id = second_cart[0]['product_id']
            self.assertNotEqual(first_product_id, second_product_id, "Users should have different products in cart")
        else:
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

    def test_12_zero_quantity(self):
        """Test adding a product with zero quantity"""
        print(f"\n🔍 Testing adding product with zero quantity...")
        
        cart_data = {
            "user_id": self.test_user_id,
            "product_id": self.test_product['id'],
            "quantity": 0
        }
        
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        # The API should either reject this with 400 or accept it but set a minimum quantity
        
        if response.status_code == 400:
            print(f"✅ API correctly rejected zero quantity with 400 error")
        else:
            self.assertEqual(response.status_code, 200, "Unexpected status code")
            cart_item = response.json()
            self.assertGreater(cart_item['quantity'], 0, "Quantity should be adjusted to at least 1")
            print(f"✅ API accepted zero quantity but adjusted to {cart_item['quantity']}")

if __name__ == '__main__':
    print(f"🚀 Testing Cart API at: {API_URL}")
    
    # Create a test suite with individual tests
    suite = unittest.TestSuite()
    
    # Add tests one by one
    test_cases = [
        CartFunctionalityTest('test_01_get_products'),
        CartFunctionalityTest('test_02_empty_cart'),
        CartFunctionalityTest('test_03_add_to_cart'),
        CartFunctionalityTest('test_04_get_cart_with_items'),
        CartFunctionalityTest('test_05_add_same_product_twice'),
        CartFunctionalityTest('test_06_add_multiple_products'),
        CartFunctionalityTest('test_07_remove_from_cart'),
        CartFunctionalityTest('test_08_clear_cart'),
        CartFunctionalityTest('test_09_add_nonexistent_product'),
        CartFunctionalityTest('test_10_cart_without_user_id'),
        CartFunctionalityTest('test_11_cart_isolation'),
        CartFunctionalityTest('test_12_zero_quantity')
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