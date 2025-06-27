import requests
import json

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
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backup status API response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Backup status API failed with status code: {response.status_code}")

if __name__ == '__main__':
    print(f"🚀 Testing Database Backup API at: {API_URL}")
    test_backup_status()