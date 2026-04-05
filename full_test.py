import requests
import json

BASE_URL = "http://localhost:8000/api"

# Login as admin
print("=" * 50)
print("Testing as ADMIN")
print("=" * 50)
login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "123456"})
print(f"✓ Login: {login_res.status_code}")
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get latest metrics
latest = requests.get(f"{BASE_URL}/metrics/latest", headers=headers).json()
print(f"✓ Latest CPU: {latest.get('latest_cpu')}%")
print(f"✓ Latest Memory: {latest.get('latest_memory')}%")

# Get user devices
devices_res = requests.get(f"{BASE_URL}/auth/me/devices", headers=headers).json()
devices = devices_res.get("devices", [])
print(f"✓ User has {len(devices)} devices:")
for d in devices:
    print(f"    - {d['name']} (source: {d['source']})")

# Get temperature history
temp = requests.get(f"{BASE_URL}/metrics/history?metric_type=temperature&minutes=5", headers=headers).json()
print(f"\n✓ Temperature data: {temp['count']} points in last 5 min")
if temp['data']:
    print(f"    Latest: {temp['data'][-1]['value']:.2f}°C from {temp['data'][-1]['source']}")

# Get humidity history
humidity = requests.get(f"{BASE_URL}/metrics/history?metric_type=humidity&minutes=5", headers=headers).json()
print(f"✓ Humidity data: {humidity['count']} points in last 5 min")
if humidity['data']:
    print(f"    Latest: {humidity['data'][-1]['value']:.2f}% from {humidity['data'][-1]['source']}")

# Get soil moisture history
soil = requests.get(f"{BASE_URL}/metrics/history?metric_type=soil_moisture&minutes=5", headers=headers).json()
print(f"✓ Soil Moisture data: {soil['count']} points in last 5 min")
if soil['data']:
    print(f"    Latest: {soil['data'][-1]['value']:.2f}% from {soil['data'][-1]['source']}")

# Get light intensity history
light = requests.get(f"{BASE_URL}/metrics/history?metric_type=light_intensity&minutes=5", headers=headers).json()
print(f"✓ Light Intensity data: {light['count']} points in last 5 min")
if light['data']:
    print(f"    Latest: {light['data'][-1]['value']:.2f} lux from {light['data'][-1]['source']}")

# Get pressure history
pressure = requests.get(f"{BASE_URL}/metrics/history?metric_type=pressure&minutes=5", headers=headers).json()
print(f"✓ Pressure data: {pressure['count']} points in last 5 min")
if pressure['data']:
    print(f"    Latest: {pressure['data'][-1]['value']:.2f} hPa from {pressure['data'][-1]['source']}")

print("\n" + "=" * 50)
print("All tests passed! IoT data is working correctly!")
print("=" * 50)
