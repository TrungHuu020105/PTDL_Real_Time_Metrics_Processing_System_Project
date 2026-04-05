import requests
import json

BASE_URL = "http://localhost:8000/api"

# Login as admin
login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "123456"})
print("Login:", login_res.status_code)
token = login_res.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get latest metrics
latest = requests.get(f"{BASE_URL}/metrics/latest", headers=headers).json()
print(f"\nLatest CPU: {latest.get('latest_cpu')}")
print(f"Latest Memory: {latest.get('latest_memory')}")

# Get temperature history
temp_res = requests.get(f"{BASE_URL}/metrics/history?metric_type=temperature&minutes=5", headers=headers)
print(f"\nTemperature response status: {temp_res.status_code}")
print(f"Temperature response: {temp_res.text[:500]}")

# Get all user devices
devices = requests.get(f"{BASE_URL}/auth/me/devices", headers=headers).json()
print(f"\nDevices for admin: {len(devices)}")
for d in devices:
    print(f"  - {d['name']} (source: {d['source']})")
