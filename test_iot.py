import requests
import json

BASE_URL = 'http://localhost:8000'

login_res = requests.post(f'{BASE_URL}/api/auth/login', json={'username': 'admin', 'password': '123456'})
token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test IoT endpoints
iot_types = ['temperature', 'humidity', 'soil_moisture', 'light_intensity', 'pressure']

for iot_type in iot_types:
    res = requests.get(f'{BASE_URL}/api/metrics/history?metric_type={iot_type}&minutes=5', headers=headers)
    data = res.json()
    count = data.get('count', 0)
    print(f"{iot_type}: {count} data points")
    if count > 0:
        print(f"  Latest: {data['data'][-1]['value']}")
