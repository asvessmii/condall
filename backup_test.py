import unittest
import requests
import json
import os
import sys
import asyncio
import time
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

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

# Add backend directory to path to import database_backup
sys.path.append('/app/backend')

class DatabaseBackupTest(unittest.TestCase):
    """Test suite for the Database Backup and Restore functionality"""

    def setUp(self):
        """Initialize test data"""
        # Define backup directory
        self.backup_dir = Path('/app/backend/data')
        
        # Test product data
        self.test_product = {
            "id": str(uuid.uuid4()),
            "name": "Backup Test Product",
            "description": "This product is used for backup testing",
            "short_description": "Backup test",
            "price": 555.55,
            "image_url": "data:image/jpeg;base64,backup_test",
            "specifications": {
                "Backup": "Test"
            },
            "created_at": datetime.utcnow()
        }
        
        # Test project data
        self.test_project = {
            "id": str(uuid.uuid4()),
            "title": "Backup Test Project",
            "description": "This project is used for backup testing",
            "address": "Backup Test Address, 123",
            "images": ["data:image/jpeg;base64,backup_test1", "data:image/jpeg;base64,backup_test2"],
            "created_at": datetime.utcnow()
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # No need to close connection here as it's handled in async methods
    
    async def insert_test_data(self):
        """Insert test data into MongoDB"""
        print("\n🔍 Inserting test data for backup testing...")
        
        # Create test data
        test_product = {
            "id": str(uuid.uuid4()),
            "name": "Backup Test Product",
            "description": "This product is used for backup testing",
            "short_description": "Backup test",
            "price": 555.55,
            "image_url": "data:image/jpeg;base64,backup_test",
            "specifications": {
                "Backup": "Test"
            },
            "created_at": datetime.utcnow()
        }
        
        test_project = {
            "id": str(uuid.uuid4()),
            "title": "Backup Test Project",
            "description": "This project is used for backup testing",
            "address": "Backup Test Address, 123",
            "images": ["data:image/jpeg;base64,backup_test1", "data:image/jpeg;base64,backup_test2"],
            "created_at": datetime.utcnow()
        }
        
        # Store IDs for later use
        self.test_product_id = test_product["id"]
        self.test_project_id = test_project["id"]
        
        # Create MongoDB client
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        try:
            # Insert test product
            await db.products.insert_one(test_product)
            print(f"✅ Test product inserted with ID: {test_product['id']}")
            
            # Insert test project
            await db.projects.insert_one(test_project)
            print(f"✅ Test project inserted with ID: {test_project['id']}")
            
            # Count documents
            products_count = await db.products.count_documents({})
            projects_count = await db.projects.count_documents({})
            print(f"✅ Database now has {products_count} products and {projects_count} projects")
        finally:
            # Close connection
            client.close()
    
    async def clean_test_data(self):
        """Clean up test data from MongoDB"""
        print("\n🔍 Cleaning up test data...")
        
        # Create MongoDB client
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        try:
            # Delete test product
            await db.products.delete_one({"id": self.test_product_id})
            print(f"✅ Test product deleted with ID: {self.test_product_id}")
            
            # Delete test project
            await db.projects.delete_one({"id": self.test_project_id})
            print(f"✅ Test project deleted with ID: {self.test_project_id}")
            
            # Count documents
            products_count = await db.products.count_documents({})
            projects_count = await db.projects.count_documents({})
            print(f"✅ Database now has {products_count} products and {projects_count} projects")
        finally:
            # Close connection
            client.close()
    
    def test_01_backup_status_api(self):
        """Test the backup status API endpoint"""
        print("\n🔍 Testing backup status API...")
        
        response = requests.get(f"{API_URL}/backup/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print(f"✅ Backup status API response: {json.dumps(data, indent=2)}")
        
        # Verify response structure
        self.assertIn("database_status", data)
        self.assertIn("backup_files", data)
        self.assertIn("backup_available", data)
        
        # Verify database status
        db_status = data["database_status"]
        self.assertIn("products", db_status)
        self.assertIn("projects", db_status)
        self.assertIn("orders", db_status)
        self.assertIn("feedback", db_status)
        self.assertIn("total", db_status)
        self.assertIn("has_data", db_status)
        
        # Verify backup files status
        backup_files = data["backup_files"]
        self.assertIn("products", backup_files)
        self.assertIn("projects", backup_files)
        self.assertIn("orders", backup_files)
        self.assertIn("feedback", backup_files)
        
        print("✅ Backup status API response structure is valid")
        return data
    
    async def test_02_create_backup_api(self):
        """Test the create backup API endpoint"""
        print("\n🔍 Testing create backup API...")
        
        # First insert test data
        await self.insert_test_data()
        
        # Get initial backup status
        initial_status = requests.get(f"{API_URL}/backup/status").json()
        print(f"✅ Initial backup status: {initial_status['backup_available']}")
        
        # Create backup
        response = requests.post(f"{API_URL}/backup/create")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print(f"✅ Create backup API response: {json.dumps(data, indent=2)}")
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("timestamp", data)
        
        # Wait a moment for backup to complete
        time.sleep(2)
        
        # Verify backup files were created
        backup_status = requests.get(f"{API_URL}/backup/status").json()
        print(f"✅ Backup status after backup: {backup_status['backup_available']}")
        
        # Check if backup files exist
        backup_files = backup_status["backup_files"]
        self.assertTrue(any(backup_files.values()), "No backup files were created")
        
        # Check if products backup file exists
        self.assertTrue(backup_files["products"], "Products backup file was not created")
        
        # Check if projects backup file exists
        self.assertTrue(backup_files["projects"], "Projects backup file was not created")
        
        print("✅ Backup files were created successfully")
        
        # Verify backup files on disk
        products_file = self.backup_dir / "products.json"
        projects_file = self.backup_dir / "projects.json"
        info_file = self.backup_dir / "backup_info.json"
        
        self.assertTrue(products_file.exists(), "Products backup file does not exist on disk")
        self.assertTrue(projects_file.exists(), "Projects backup file does not exist on disk")
        self.assertTrue(info_file.exists(), "Backup info file does not exist on disk")
        
        print("✅ Backup files exist on disk")
        
        # Verify backup info file
        with open(info_file, 'r') as f:
            backup_info = json.load(f)
        
        self.assertIn("timestamp", backup_info)
        self.assertIn("collections", backup_info)
        self.assertIn("products", backup_info["collections"])
        self.assertIn("projects", backup_info["collections"])
        
        print(f"✅ Backup info file is valid: {json.dumps(backup_info, indent=2)}")
        
        # Verify products backup file contains our test product
        with open(products_file, 'r') as f:
            products_data = json.load(f)
        
        test_product_found = False
        for product in products_data:
            if product.get("id") == self.test_product["id"]:
                test_product_found = True
                break
        
        self.assertTrue(test_product_found, "Test product not found in backup file")
        print("✅ Test product found in backup file")
        
        # Verify projects backup file contains our test project
        with open(projects_file, 'r') as f:
            projects_data = json.load(f)
        
        test_project_found = False
        for project in projects_data:
            if project.get("id") == self.test_project["id"]:
                test_project_found = True
                break
        
        self.assertTrue(test_project_found, "Test project not found in backup file")
        print("✅ Test project found in backup file")
        
        return data
    
    async def test_03_restore_backup_api(self):
        """Test the restore backup API endpoint"""
        print("\n🔍 Testing restore backup API...")
        
        # Create MongoDB client
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        try:
            # First clean up test data
            await self.clean_test_data()
            
            # Verify test data is gone
            product = await db.products.find_one({"id": self.test_product_id})
            project = await db.projects.find_one({"id": self.test_project_id})
            
            self.assertIsNone(product, "Test product still exists after cleanup")
            self.assertIsNone(project, "Test project still exists after cleanup")
            print("✅ Test data successfully cleaned up")
            
            # Get initial counts
            initial_products_count = await db.products.count_documents({})
            initial_projects_count = await db.projects.count_documents({})
            print(f"✅ Initial counts: {initial_products_count} products, {initial_projects_count} projects")
            
            # Restore backup
            response = requests.post(f"{API_URL}/backup/restore")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"✅ Restore backup API response: {json.dumps(data, indent=2)}")
            
            # Verify response structure
            self.assertIn("message", data)
            self.assertIn("products_count", data)
            self.assertIn("projects_count", data)
            
            # Wait a moment for restore to complete
            time.sleep(2)
            
            # Verify test data is restored
            product = await db.products.find_one({"id": self.test_product_id})
            project = await db.projects.find_one({"id": self.test_project_id})
            
            self.assertIsNotNone(product, "Test product was not restored")
            self.assertIsNotNone(project, "Test project was not restored")
            
            print("✅ Test data successfully restored")
            
            # Verify counts
            final_products_count = await db.products.count_documents({})
            final_projects_count = await db.projects.count_documents({})
            print(f"✅ Final counts: {final_products_count} products, {final_projects_count} projects")
            
            # Verify counts match response
            self.assertEqual(final_products_count, data["products_count"])
            self.assertEqual(final_projects_count, data["projects_count"])
            
            print("✅ Database counts match response")
            
            return data
        finally:
            # Close connection
            client.close()

async def run_async_tests():
    """Run the async test methods"""
    test = DatabaseBackupTest()
    
    try:
        # Run tests in sequence
        await test.test_02_create_backup_api()
        await test.test_03_restore_backup_api()
    except Exception as e:
        print(f"Error during async tests: {e}")
        raise

if __name__ == '__main__':
    print(f"🚀 Testing Database Backup and Restore API at: {API_URL}")
    
    # Run async tests
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_async_tests())
    
    # Run regular tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)