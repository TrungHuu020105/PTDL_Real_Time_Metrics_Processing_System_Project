import requests
import json

BASE_URL = 'http://localhost:8000'

login_res = requests.post(f'{BASE_URL}/api/auth/login', json={'username': 'admin', 'password': '123456'})
token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Check latest metrics
metrics_res = requests.get(f'{BASE_URL}/api/metrics/latest', headers=headers)
print(f"Latest Metrics Status: {metrics_res.status_code}")
metrics = metrics_res.json()
print(f"CPU: {metrics.get('latest_cpu')}")
print(f"Memory: {metrics.get('latest_memory')}")

# Check history
history_res = requests.get(f'{BASE_URL}/api/metrics/history?metric_type=cpu&minutes=5', headers=headers)
print(f"\nHistory Status: {history_res.status_code}")
history = history_res.json()
print(f"CPU data points: {history.get('count')}")
if history.get('count', 0) > 0:
    print(f"First: {history['data'][0]['value']}")
    print(f"Last: {history['data'][-1]['value']}")
