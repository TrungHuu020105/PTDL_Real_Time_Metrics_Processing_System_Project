import requests
import json

BASE_URL = 'http://localhost:8000'

# Test login
login_res = requests.post(f'{BASE_URL}/api/auth/login', json={'username': 'admin', 'password': '123456'})
if login_res.status_code != 200:
    print("Login failed")
    exit(1)

token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print("✓ Login successful")

# Check devices
dev_res = requests.get(f'{BASE_URL}/api/admin/devices', headers=headers)
devices = dev_res.json().get('devices', [])
print(f"✓ Found {len(devices)} devices")
for d in devices:
    print(f"  - {d.get('name')} ({d.get('source')})")

# Check admin's accessible devices
my_dev_res = requests.get(f'{BASE_URL}/api/auth/me/devices', headers=headers)
my_devices = my_dev_res.json().get('devices', [])
print(f"✓ Admin has access to {len(my_devices)} devices")
