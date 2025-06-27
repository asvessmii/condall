import requests
import unittest
import json
import sys
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class CartIsolationTest(unittest.TestCase):
    """Test suite for cart isolation functionality"""

    def setUp(self):
        """Initialize test data"""
        # Get available products for testing
        response = requests.get(f"{API_URL}/products")
        self.products = response.json()
        if not self.products:
            self.fail("No products available for testing")
        
        # Define test users
        self.user1_id = "test_user_1"
        self.user2_id = "test_user_2"
        
        # Clean up any existing cart items for test users
        requests.delete(f"{API_URL}/cart?user_id={self.user1_id}")
        requests.delete(f"{API_URL}/cart?user_id={self.user2_id}")
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear carts after tests
        requests.delete(f"{API_URL}/cart?user_id={self.user1_id}")
        requests.delete(f"{API_URL}/cart?user_id={self.user2_id}")

    def test_01_cart_isolation(self):
        """Test that carts are isolated between users"""
        print("\n🔍 Testing cart isolation between users...")
        
        # Add product to user1's cart
        product1 = self.products[0]
        cart_data1 = {
            "user_id": self.user1_id,
            "product_id": product1['id'],
            "quantity": 2
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data1)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Added product '{product1['name']}' to user1's cart")
        
        # Add different product to user2's cart
        product2 = self.products[1] if len(self.products) > 1 else self.products[0]
        cart_data2 = {
            "user_id": self.user2_id,
            "product_id": product2['id'],
            "quantity": 3
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data2)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Added product '{product2['name']}' to user2's cart")
        
        # Check user1's cart
        response = requests.get(f"{API_URL}/cart?user_id={self.user1_id}")
        self.assertEqual(response.status_code, 200)
        user1_cart = response.json()
        self.assertEqual(len(user1_cart), 1)
        self.assertEqual(user1_cart[0]['product_id'], product1['id'])
        self.assertEqual(user1_cart[0]['quantity'], 2)
        print(f"✅ User1's cart contains only their product: {user1_cart[0]['product_name']}")
        
        # Check user2's cart
        response = requests.get(f"{API_URL}/cart?user_id={self.user2_id}")
        self.assertEqual(response.status_code, 200)
        user2_cart = response.json()
        self.assertEqual(len(user2_cart), 1)
        self.assertEqual(user2_cart[0]['product_id'], product2['id'])
        self.assertEqual(user2_cart[0]['quantity'], 3)
        print(f"✅ User2's cart contains only their product: {user2_cart[0]['product_name']}")
        
        print("✅ Cart isolation test passed - each user sees only their own cart items")

    def test_02_duplicate_item_handling(self):
        """Test that adding the same product twice increases quantity instead of creating duplicates"""
        print("\n🔍 Testing duplicate item handling...")
        
        # Add product to user's cart
        product = self.products[0]
        cart_data = {
            "user_id": self.user1_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Added product '{product['name']}' to cart with quantity 1")
        
        # Add the same product again
        cart_data = {
            "user_id": self.user1_id,
            "product_id": product['id'],
            "quantity": 2
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Added the same product again with quantity 2")
        
        # Check cart
        response = requests.get(f"{API_URL}/cart?user_id={self.user1_id}")
        self.assertEqual(response.status_code, 200)
        cart_items = response.json()
        self.assertEqual(len(cart_items), 1)  # Should still be only 1 item
        self.assertEqual(cart_items[0]['quantity'], 3)  # Quantity should be 1+2=3
        print(f"✅ Cart contains 1 item with quantity 3: {cart_items[0]['product_name']}")
        
        print("✅ Duplicate item handling test passed - quantity was increased instead of creating duplicate")

    def test_03_user_id_validation(self):
        """Test that requests without user_id return 400 error"""
        print("\n🔍 Testing user_id validation...")
        
        # Try to get cart without user_id
        response = requests.get(f"{API_URL}/cart")
        self.assertIn(response.status_code, [400, 422])  # Accept either 400 or 422 (Unprocessable Entity)
        print(f"✅ GET /cart without user_id returns {response.status_code} error")
        
        # Try to add to cart without user_id
        product = self.products[0]
        cart_data = {
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertIn(response.status_code, [400, 422])  # Accept either 400 or 422
        print(f"✅ POST /cart without user_id returns {response.status_code} error")
        
        # Try to remove from cart without user_id
        # First add an item to cart
        cart_data = {
            "user_id": self.user1_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        cart_item = response.json()
        
        # Try to delete without user_id
        response = requests.delete(f"{API_URL}/cart/{cart_item['id']}")
        self.assertIn(response.status_code, [400, 422])  # Accept either 400 or 422
        print(f"✅ DELETE /cart/{{item_id}} without user_id returns {response.status_code} error")
        
        # Try to clear cart without user_id
        response = requests.delete(f"{API_URL}/cart")
        self.assertIn(response.status_code, [400, 422])  # Accept either 400 or 422
        print(f"✅ DELETE /cart without user_id returns {response.status_code} error")
        
        print("✅ User ID validation test passed - all endpoints require user_id")

    def test_04_cross_user_item_deletion(self):
        """Test that a user cannot delete another user's cart items"""
        print("\n🔍 Testing cross-user item deletion prevention...")
        
        # Add product to user1's cart
        product = self.products[0]
        cart_data = {
            "user_id": self.user1_id,
            "product_id": product['id'],
            "quantity": 1
        }
        response = requests.post(f"{API_URL}/cart", json=cart_data)
        self.assertEqual(response.status_code, 200)
        cart_item = response.json()
        print(f"✅ Added product '{product['name']}' to user1's cart")
        
        # Try to delete the item using user2's ID
        response = requests.delete(f"{API_URL}/cart/{cart_item['id']}?user_id={self.user2_id}")
        self.assertEqual(response.status_code, 404)
        print("✅ User2 cannot delete user1's cart item (404 error)")
        
        # Verify item still exists in user1's cart
        response = requests.get(f"{API_URL}/cart?user_id={self.user1_id}")
        self.assertEqual(response.status_code, 200)
        cart_items = response.json()
        self.assertEqual(len(cart_items), 1)
        print("✅ Item still exists in user1's cart")
        
        print("✅ Cross-user item deletion prevention test passed")

    def test_05_cart_clearing(self):
        """Test that clearing a cart only affects the specified user"""
        print("\n🔍 Testing cart clearing isolation...")
        
        # Add products to both users' carts
        product1 = self.products[0]
        product2 = self.products[1] if len(self.products) > 1 else self.products[0]
        
        # Add to user1's cart
        cart_data1 = {
            "user_id": self.user1_id,
            "product_id": product1['id'],
            "quantity": 1
        }
        requests.post(f"{API_URL}/cart", json=cart_data1)
        print(f"✅ Added product '{product1['name']}' to user1's cart")
        
        # Add to user2's cart
        cart_data2 = {
            "user_id": self.user2_id,
            "product_id": product2['id'],
            "quantity": 1
        }
        requests.post(f"{API_URL}/cart", json=cart_data2)
        print(f"✅ Added product '{product2['name']}' to user2's cart")
        
        # Clear user1's cart
        response = requests.delete(f"{API_URL}/cart?user_id={self.user1_id}")
        self.assertEqual(response.status_code, 200)
        print("✅ Cleared user1's cart")
        
        # Verify user1's cart is empty
        response = requests.get(f"{API_URL}/cart?user_id={self.user1_id}")
        self.assertEqual(response.status_code, 200)
        user1_cart = response.json()
        self.assertEqual(len(user1_cart), 0)
        print("✅ User1's cart is empty")
        
        # Verify user2's cart is still intact
        response = requests.get(f"{API_URL}/cart?user_id={self.user2_id}")
        self.assertEqual(response.status_code, 200)
        user2_cart = response.json()
        self.assertEqual(len(user2_cart), 1)
        print("✅ User2's cart still has items")
        
        print("✅ Cart clearing isolation test passed - only specified user's cart was cleared")

if __name__ == '__main__':
    print(f"🚀 Testing Cart Isolation at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)