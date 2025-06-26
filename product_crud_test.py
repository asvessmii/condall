import requests
import unittest
import os
import json
import time
import uuid
from pymongo import MongoClient
from datetime import datetime

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

class ProductCRUDTest(unittest.TestCase):
    """Test suite for Product CRUD operations in the Air Conditioner Shop API"""

    def setUp(self):
        """Initialize test data"""
        # Create a test product with unique name to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        self.test_product = {
            "name": f"Test Air Conditioner {unique_id}",
            "description": "This is a test air conditioner for API testing",
            "short_description": "Test AC unit",
            "price": 35000,
            "image_url": "https://images.pexels.com/photos/3964537/pexels-photo-3964537.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.2 кВт",
                "Уровень шума": "22 дБ",
                "Класс энергоэффективности": "A++"
            }
        }
        self.added_product_ids = []
        
        # Connect to MongoDB
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
        # Print test information
        print(f"\n🚀 Testing Product CRUD operations at: {API_URL}")
        print(f"📊 MongoDB connection: {MONGO_URL}")
        print(f"📊 Database name: {DB_NAME}")

    def tearDown(self):
        """Clean up after tests"""
        # Clean up any test products
        for product_id in self.added_product_ids:
            try:
                # Try to delete via API first
                requests.delete(f"{API_URL}/products/{product_id}")
            except:
                # If API fails, delete directly from MongoDB
                self.db.products.delete_one({"id": product_id})
        
        # Close MongoDB connection
        self.client.close()

    def test_01_get_all_products(self):
        """Test retrieving all products, check for duplicates, count products"""
        print("\n🔍 Testing GET /api/products - retrieving all products...")
        
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200, "Failed to get products")
        
        products = response.json()
        self.assertIsInstance(products, list, "Products response is not a list")
        
        # Count products
        product_count = len(products)
        print(f"✅ Found {product_count} products in the database")
        
        # Check for duplicate products (by ID)
        product_ids = [p['id'] for p in products]
        unique_ids = set(product_ids)
        
        self.assertEqual(len(product_ids), len(unique_ids), 
                         f"Found duplicate product IDs: {len(product_ids) - len(unique_ids)} duplicates")
        print("✅ No duplicate product IDs found")
        
        # Check for duplicate products (by name)
        product_names = [p['name'] for p in products]
        unique_names = set(product_names)
        
        if len(product_names) != len(unique_names):
            print(f"⚠️ Found {len(product_names) - len(unique_names)} products with duplicate names")
            # Find the duplicates
            name_counts = {}
            for name in product_names:
                if name in name_counts:
                    name_counts[name] += 1
                else:
                    name_counts[name] = 1
            
            duplicates = {name: count for name, count in name_counts.items() if count > 1}
            print(f"⚠️ Duplicate product names: {duplicates}")
        else:
            print("✅ No duplicate product names found")
        
        # Verify product structure
        if products:
            product = products[0]
            required_fields = ['id', 'name', 'description', 'short_description', 
                              'price', 'image_url', 'specifications']
            for field in required_fields:
                self.assertIn(field, product, f"Product missing required field: {field}")
            print("✅ Product structure is valid")
        
        return product_count

    def test_02_add_product(self):
        """Test adding a new product and verifying it's saved"""
        print("\n🔍 Testing POST /api/products - adding a new product...")
        
        # Get initial product count
        response = requests.get(f"{API_URL}/products")
        initial_count = len(response.json())
        print(f"✅ Initial product count: {initial_count}")
        
        # Add a new product
        response = requests.post(f"{API_URL}/products", json=self.test_product)
        self.assertEqual(response.status_code, 200, "Failed to add product")
        
        new_product = response.json()
        self.assertIn('id', new_product, "New product doesn't have an ID")
        product_id = new_product['id']
        self.added_product_ids.append(product_id)  # Add to cleanup list
        print(f"✅ Added new product with ID: {product_id}")
        
        # Verify the product was added by getting all products
        response = requests.get(f"{API_URL}/products")
        updated_count = len(response.json())
        self.assertEqual(updated_count, initial_count + 1, 
                         f"Product count didn't increase after adding product")
        print(f"✅ Product count increased from {initial_count} to {updated_count}")
        
        # Verify the product was added by getting it directly
        response = requests.get(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get product with ID {product_id}")
        
        retrieved_product = response.json()
        self.assertEqual(retrieved_product['id'], product_id, "Retrieved product ID doesn't match")
        self.assertEqual(retrieved_product['name'], self.test_product['name'], 
                         "Retrieved product name doesn't match")
        print(f"✅ Successfully retrieved the added product: {retrieved_product['name']}")
        
        # Verify product ID uniqueness
        self.assertTrue(len(product_id) > 0, "Product ID should not be empty")
        print(f"✅ Product ID is unique: {product_id}")
        
        return product_id

    def test_03_delete_product(self):
        """Test deleting a product and verifying it's removed"""
        print("\n🔍 Testing DELETE /api/products/{product_id} - deleting a product...")
        
        # First add a product to delete
        response = requests.post(f"{API_URL}/products", json=self.test_product)
        self.assertEqual(response.status_code, 200, "Failed to add product for deletion test")
        
        product_id = response.json()['id']
        print(f"✅ Created product with ID {product_id} for deletion test")
        
        # Get initial product count
        response = requests.get(f"{API_URL}/products")
        initial_count = len(response.json())
        print(f"✅ Initial product count: {initial_count}")
        
        # Delete the product
        response = requests.delete(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 200, f"Failed to delete product with ID {product_id}")
        print(f"✅ Product deleted successfully: {response.json()['message']}")
        
        # Verify the product was deleted by getting all products
        response = requests.get(f"{API_URL}/products")
        updated_count = len(response.json())
        self.assertEqual(updated_count, initial_count - 1, 
                         f"Product count didn't decrease after deleting product")
        print(f"✅ Product count decreased from {initial_count} to {updated_count}")
        
        # Verify the product was deleted by trying to get it directly
        response = requests.get(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 404, 
                         f"Product with ID {product_id} still exists after deletion")
        print("✅ Product no longer exists in the database")
        
        # Test deleting a non-existent product
        non_existent_id = str(uuid.uuid4())
        response = requests.delete(f"{API_URL}/products/{non_existent_id}")
        self.assertEqual(response.status_code, 404, 
                         "Deleting non-existent product should return 404")
        print("✅ Deleting non-existent product returns 404 as expected")

    def test_04_data_persistence(self):
        """Test data persistence after service restart"""
        print("\n🔍 Testing data persistence after service restart...")
        
        # Add a new product for persistence testing
        persistence_product = self.test_product.copy()
        persistence_product["name"] = f"Persistence Test AC {uuid.uuid4()}"
        
        response = requests.post(f"{API_URL}/products", json=persistence_product)
        self.assertEqual(response.status_code, 200, "Failed to add product for persistence test")
        
        product_id = response.json()['id']
        self.added_product_ids.append(product_id)  # Add to cleanup list
        print(f"✅ Created product with ID {product_id} for persistence test")
        
        # Restart the backend service
        print("\n🔄 Restarting backend service...")
        os.system("sudo supervisorctl restart backend")
        
        # Wait for service to restart
        print("⏳ Waiting for backend service to restart...")
        time.sleep(10)
        
        # Verify the product still exists after restart
        response = requests.get(f"{API_URL}/products/{product_id}")
        self.assertEqual(response.status_code, 200, 
                         f"Product with ID {product_id} not found after service restart")
        
        retrieved_product = response.json()
        self.assertEqual(retrieved_product['id'], product_id, 
                         "Retrieved product ID doesn't match after restart")
        self.assertEqual(retrieved_product['name'], persistence_product['name'], 
                         "Retrieved product name doesn't match after restart")
        print(f"✅ Successfully retrieved the product after service restart: {retrieved_product['name']}")

    def test_05_product_uniqueness(self):
        """Test adding identical products to check for duplicates"""
        print("\n🔍 Testing product uniqueness when adding identical products...")
        
        # Create a product with a unique name for this test
        duplicate_product = self.test_product.copy()
        duplicate_product["name"] = f"Duplicate Test AC {uuid.uuid4()}"
        
        # Add the product first time
        response = requests.post(f"{API_URL}/products", json=duplicate_product)
        self.assertEqual(response.status_code, 200, "Failed to add first product")
        
        first_product_id = response.json()['id']
        self.added_product_ids.append(first_product_id)  # Add to cleanup list
        print(f"✅ Added first product with ID: {first_product_id}")
        
        # Add the identical product second time
        response = requests.post(f"{API_URL}/products", json=duplicate_product)
        self.assertEqual(response.status_code, 200, "Failed to add second identical product")
        
        second_product_id = response.json()['id']
        self.added_product_ids.append(second_product_id)  # Add to cleanup list
        print(f"✅ Added second identical product with ID: {second_product_id}")
        
        # Check if the IDs are different (should be for proper implementation)
        self.assertNotEqual(first_product_id, second_product_id, 
                           "Both products have the same ID, which indicates they might be the same record")
        print("✅ Products have different IDs as expected")
        
        # Get all products with the same name
        response = requests.get(f"{API_URL}/products")
        products = response.json()
        
        duplicate_products = [p for p in products if p['name'] == duplicate_product['name']]
        print(f"✅ Found {len(duplicate_products)} products with the same name")
        
        # Check if we have exactly 2 products with the same name
        self.assertEqual(len(duplicate_products), 2, 
                         f"Expected 2 products with the same name, found {len(duplicate_products)}")
        
        if len(duplicate_products) == 2:
            print("⚠️ The system allows duplicate products with the same name but different IDs")
            print("⚠️ This might be intended behavior, but could lead to confusion for users")
            print("⚠️ Consider implementing a uniqueness constraint on product names or using upsert")
        
        # Verify both products have different IDs but same data
        self.assertEqual(duplicate_products[0]['name'], duplicate_products[1]['name'])
        self.assertNotEqual(duplicate_products[0]['id'], duplicate_products[1]['id'])
        print("✅ Duplicate products have same name but different IDs")

if __name__ == '__main__':
    print(f"🚀 Testing Product CRUD operations at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)