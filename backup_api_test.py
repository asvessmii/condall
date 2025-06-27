import requests
import json
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

def test_backup_status():
    """Test the backup status API endpoint"""
    print("\n🔍 Testing backup status API...")
    
    response = requests.get(f"{API_URL}/backup/status")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backup status API response: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Backup status API failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_create_backup():
    """Test the create backup API endpoint"""
    print("\n🔍 Testing create backup API...")
    
    response = requests.post(f"{API_URL}/backup/create")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Create backup API response: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Create backup API failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_restore_backup():
    """Test the restore backup API endpoint"""
    print("\n🔍 Testing restore backup API...")
    
    response = requests.post(f"{API_URL}/backup/restore")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Restore backup API response: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Restore backup API failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == '__main__':
    print(f"🚀 Testing Database Backup API at: {API_URL}")
    
    # Test backup status
    initial_status = test_backup_status()
    
    # Test create backup
    create_result = test_create_backup()
    
    # Wait a moment for backup to complete
    if create_result:
        print("\n⏳ Waiting for backup to complete...")
        time.sleep(2)
        
        # Test backup status again
        after_create_status = test_backup_status()
        
        # Test restore backup
        restore_result = test_restore_backup()
        
        # Wait a moment for restore to complete
        if restore_result:
            print("\n⏳ Waiting for restore to complete...")
            time.sleep(2)
            
            # Test backup status again
            after_restore_status = test_backup_status()