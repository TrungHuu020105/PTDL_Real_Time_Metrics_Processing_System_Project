import requests

BASE_URL = "http://localhost:8000/api"

# Login as admin
login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "123456"})
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing new admin features:")
print("=" * 60)

# Test 1: Get alert thresholds
print("\n1. Testing GET alert thresholds:")
thresholds_res = requests.get(f"{BASE_URL}/admin/alert-thresholds", headers=headers).json()
print(f"   ✓ Found {thresholds_res['count']} alert thresholds")
if thresholds_res['thresholds']:
    t = thresholds_res['thresholds'][0]
    print(f"   Example: {t['metric_type']} - warning: {t.get('warning_threshold')}, critical: {t.get('critical_threshold')}")

# Test 2: Update alert threshold
print("\n2. Testing UPDATE alert threshold:")
update_res = requests.put(
    f"{BASE_URL}/admin/alert-thresholds/cpu?warning_threshold=75&critical_threshold=85",
    headers=headers
).json()
print(f"   ✓ Updated CPU threshold: warning={update_res['threshold']['warning_threshold']}, critical={update_res['threshold']['critical_threshold']}")

# Test 3: Create test user
print("\n3. Testing CHANGE user role:")
register_res = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "roletest",
    "email": "roletest@example.com",
    "password": "password123",
    "role": "user"
})
test_user_id = register_res.json()['id']
print(f"   Created test user (id: {test_user_id}, role: user)")

# Approve the user first
approve_res = requests.post(f"{BASE_URL}/admin/users/{test_user_id}/approve", headers=headers)
print(f"   Approved user")

# Change role to admin
role_change_res = requests.put(
    f"{BASE_URL}/admin/users/{test_user_id}/role?role=admin",
    headers=headers
).json()
print(f"   ✓ Changed role to: {role_change_res['user']['role']}")

# Change back to user
role_change_back = requests.put(
    f"{BASE_URL}/admin/users/{test_user_id}/role?role=user",
    headers=headers
).json()
print(f"   ✓ Changed role back to: {role_change_back['user']['role']}")

print("\n" + "=" * 60)
print("All new features tested successfully!")
