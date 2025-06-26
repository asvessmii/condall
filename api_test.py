import requests
import unittest
import json
import uuid
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class AirConditionerShopAPITest(unittest.TestCase):
    """Test suite for the Air Conditioner Shop API"""

    def setUp(self):
        """Initialize test data"""
        self.test_product = {
            "name": "API Test Product",
            "description": "This is a test product created via API",
            "short_description": "API test product",
            "price": 555.55,
            "image_url": "data:image/jpeg;base64,api_test",
            "specifications": {
                "API Test": "Value"
            }
        }
        
        self.test_project = {
            "title": "API Test Project",
            "description": "This is a test project created via API",
            "address": "API Test Address, 789",
            "images": ["data:image/jpeg;base64,api_test1", "data:image/jpeg;base64,api_test2"]
        }
        
    def tearDown(self):
        """Clean up after tests"""
        # Clean up test data
        pass

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ API root endpoint works: {data['message']}")

    def test_02_get_products(self):
        """Test getting all products"""
        print("\n🔍 Testing products endpoint...")
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertIsInstance(products, list)
        print(f"✅ Products endpoint returned {len(products)} products")
        
        # Verify product structure
        if products:
            product = products[0]
            required_fields = ['id', 'name', 'description', 'short_description', 'price', 'image_url', 'specifications']
            for field in required_fields:
                self.assertIn(field, product)
            print("✅ Product structure is valid")
        
        return products

    def test_03_get_projects(self):
        """Test getting all projects"""
        print("\n🔍 Testing projects endpoint...")
        response = requests.get(f"{API_URL}/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.json()
        self.assertIsInstance(projects, list)
        print(f"✅ Projects endpoint returned {len(projects)} projects")
        
        # Verify project structure
        if projects:
            project = projects[0]
            required_fields = ['id', 'title', 'description', 'address', 'images']
            for field in required_fields:
                self.assertIn(field, project)
            print("✅ Project structure is valid")
        
        return projects

    def test_04_create_product(self):
        """Test creating a product via API"""
        print("\n🔍 Testing product creation via API...")
        
        # Create product
        response = requests.post(f"{API_URL}/products", json=self.test_product)
        self.assertEqual(response.status_code, 200)
        created_product = response.json()
        
        # Verify created product
        self.assertIn("id", created_product)
        self.assertEqual(created_product["name"], self.test_product["name"])
        self.assertEqual(created_product["price"], self.test_product["price"])
        print(f"✅ Product created via API with ID: {created_product['id']}")
        
        # Verify product exists in database
        response = requests.get(f"{API_URL}/products/{created_product['id']}")
        self.assertEqual(response.status_code, 200)
        retrieved_product = response.json()
        self.assertEqual(retrieved_product["id"], created_product["id"])
        print("✅ Product verified in database")
        
        # Clean up - delete the test product
        # Note: There's no delete endpoint in the API, so we can't clean up here
        
        return created_product["id"]

    def test_05_create_project(self):
        """Test creating a project via API"""
        print("\n🔍 Testing project creation via API...")
        
        # Generate UUID for project
        self.test_project["id"] = str(uuid.uuid4())
        
        # Create project
        response = requests.post(f"{API_URL}/projects", json=self.test_project)
        self.assertEqual(response.status_code, 200)
        created_project = response.json()
        
        # Verify created project
        self.assertEqual(created_project["id"], self.test_project["id"])
        self.assertEqual(created_project["title"], self.test_project["title"])
        print(f"✅ Project created via API with ID: {created_project['id']}")
        
        # Verify project exists in database by getting all projects
        response = requests.get(f"{API_URL}/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.json()
        
        found = False
        for project in projects:
            if project["id"] == created_project["id"]:
                found = True
                break
        
        self.assertTrue(found, "Project not found in database after creation")
        print("✅ Project verified in database")
        
        return created_project["id"]

    def test_06_persistence_after_restart(self):
        """Test data persistence after service restart"""
        print("\n🔍 Testing data persistence after restart...")
        
        # Create a product for persistence testing
        persistence_product = {
            "name": "Persistence API Test Product",
            "description": "This product tests API persistence after restart",
            "short_description": "API persistence test",
            "price": 444.44,
            "image_url": "data:image/jpeg;base64,api_persistence_test",
            "specifications": {
                "API Persistence": "Test"
            }
        }
        
        # Create the product
        response = requests.post(f"{API_URL}/products", json=persistence_product)
        self.assertEqual(response.status_code, 200)
        created_product = response.json()
        product_id = created_product["id"]
        print(f"✅ Created persistence test product with ID: {product_id}")
        
        # Get all products before restart
        response = requests.get(f"{API_URL}/products")
        products_before = response.json()
        products_count_before = len(products_before)
        print(f"✅ Products count before restart: {products_count_before}")
        
        # Restart services
        print("\n🔄 Restarting services...")
        import os
        os.system("sudo supervisorctl restart all")
        
        # Wait for services to restart
        print("Waiting for services to restart...")
        time.sleep(10)
        
        # Get all products after restart
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200)
        products_after = response.json()
        products_count_after = len(products_after)
        print(f"✅ Products count after restart: {products_count_after}")
        
        # Verify our test product still exists
        found = False
        for product in products_after:
            if product["id"] == product_id:
                found = True
                break
        
        self.assertTrue(found, "Persistence test product not found after restart")
        print("✅ Persistence test product found after restart")

if __name__ == "__main__":
    print(f"🚀 Testing API at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)