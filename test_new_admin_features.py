import requests

BASE_URL = "http://localhost:8000/api"

# Login as admin
login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "123456"})
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing new admin endpoints:")
print("=" * 50)

# Test 1: Update device name
print("\n1. Testing UPDATE device name:")
devices_res = requests.get(f"{BASE_URL}/admin/devices", headers=headers).json()
if devices_res['devices']:
    device = devices_res['devices'][0]
    print(f"   Original: {device['name']}")
    
    update_res = requests.put(
        f"{BASE_URL}/admin/devices/{device['id']}", 
        json={"name": "Updated Device Name"},
        headers=headers
    )
    if update_res.status_code == 200:
        print(f"   ✓ Updated to: {update_res.json()['name']}")
    else:
        print(f"   ✗ Failed: {update_res.text}")

# Test 2: Create a test user, then delete it
print("\n2. Testing DELETE user:")
# Create a test user first
register_res = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser123",
    "email": "test123@example.com",
    "password": "password123",
    "role": "user"
})

if register_res.status_code == 201:
    test_user_id = register_res.json()['id']
    print(f"   Created test user (id: {test_user_id})")
    
    # Delete the user
    delete_res = requests.delete(f"{BASE_URL}/admin/users/{test_user_id}", headers=headers)
    if delete_res.status_code == 200:
        print(f"   ✓ User deleted successfully")
    else:
        print(f"   ✗ Failed to delete: {delete_res.text}")
else:
    print(f"   ✗ Failed to create test user")

print("\n" + "=" * 50)
print("All tests completed!")
