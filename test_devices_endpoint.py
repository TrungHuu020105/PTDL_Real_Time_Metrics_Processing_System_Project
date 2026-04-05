import requests

BASE_URL = 'http://localhost:8000'

login_res = requests.post(f'{BASE_URL}/api/auth/login', json={'username': 'admin', 'password': '123456'})
token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Check the actual response
my_dev_res = requests.get(f'{BASE_URL}/api/auth/me/devices', headers=headers)
print(f"Status: {my_dev_res.status_code}")
print(f"Content-Type: {my_dev_res.headers.get('content-type')}")
print(f"Response text: {my_dev_res.text}")
