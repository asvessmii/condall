import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime
import json

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

async def test_mongodb_connection():
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
        
        return client, db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None, None

async def test_product_crud(db):
    """Test CRUD operations for products"""
    print("\n🔍 Testing product CRUD operations...")
    
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

async def test_project_crud(db):
    """Test CRUD operations for projects"""
    print("\n🔍 Testing project CRUD operations...")
    
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

async def test_persistence(db):
    """Test data persistence after service restart"""
    print("\n🔍 Testing data persistence...")
    
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

async def main():
    print("🚀 Starting MongoDB Tests")
    
    # Test MongoDB connection
    client, db = await test_mongodb_connection()
    if not client or not db:
        print("❌ Cannot proceed with tests due to connection failure")
        return
    
    # Test CRUD operations
    await test_product_crud(db)
    await test_project_crud(db)
    
    # Test persistence
    await test_persistence(db)
    
    # Close connection
    client.close()
    print("\n✅ All MongoDB tests completed")

if __name__ == "__main__":
    asyncio.run(main())