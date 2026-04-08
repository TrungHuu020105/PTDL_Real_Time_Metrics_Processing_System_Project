"""Test subscription request workflow"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test user and admin tokens (update these with actual tokens)
USER_TOKEN = None
ADMIN_TOKEN = None
USER_ID = None
ADMIN_ID = None
SERVER_ID = None
REQUEST_ID = None


def register_and_login_user(email, password, username):
    """Register and login a user"""
    # Register
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": password, "username": username}
    )
    print(f"Register user: {response.status_code}")
    
    # Login
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    print(f"Login user: {response.status_code}")
    data = response.json()
    return data.get("access_token"), data.get("user", {}).get("id")


def get_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}


def test_user_creates_request():
    """Test 1: User creates a subscription request"""
    global REQUEST_ID
    
    print("\n=== TEST 1: User Creates Subscription Request ===")
    
    response = requests.post(
        f"{BASE_URL}/api/servers/requests",
        json={"server_id": SERVER_ID},
        headers=get_headers(USER_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        REQUEST_ID = response.json().get("id")
        print(f"✓ Request created with ID: {REQUEST_ID}")
        return True
    else:
        print("✗ Failed to create request")
        return False


def test_user_views_requests():
    """Test 2: User views their subscription requests"""
    print("\n=== TEST 2: User Views Subscription Requests ===")
    
    response = requests.get(
        f"{BASE_URL}/api/servers/requests",
        headers=get_headers(USER_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        requests_list = response.json().get("requests", [])
        print(f"✓ Found {len(requests_list)} request(s)")
        for req in requests_list:
            print(f"  - {req['server_name']}: {req['status']}")
        return True
    else:
        print("✗ Failed to fetch requests")
        return False


def test_admin_views_pending_requests():
    """Test 3: Admin views pending subscription requests"""
    print("\n=== TEST 3: Admin Views Pending Requests ===")
    
    response = requests.get(
        f"{BASE_URL}/api/servers/admin/requests/pending",
        headers=get_headers(ADMIN_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        requests_list = response.json().get("requests", [])
        print(f"✓ Found {len(requests_list)} pending request(s)")
        return True
    else:
        print("✗ Failed to fetch pending requests")
        return False


def test_admin_approves_request():
    """Test 4: Admin approves a subscription request"""
    global REQUEST_ID
    
    print("\n=== TEST 4: Admin Approves Request ===")
    
    response = requests.put(
        f"{BASE_URL}/api/servers/admin/requests/{REQUEST_ID}/approve",
        headers=get_headers(ADMIN_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print(f"✓ Request approved")
        return True
    else:
        print("✗ Failed to approve request")
        return False


def test_user_sees_approved_status():
    """Test 5: User sees their request is approved"""
    print("\n=== TEST 5: User Sees Approved Status ===")
    
    response = requests.get(
        f"{BASE_URL}/api/servers/requests",
        headers=get_headers(USER_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        approved_requests = [r for r in data.get("requests", []) if r["status"] == "approved"]
        print(f"✓ Found {len(approved_requests)} approved request(s)")
        for req in approved_requests:
            print(f"  - {req['server_name']}: {req['status']} at {req['approved_at']}")
        return True
    else:
        print("✗ Failed to fetch requests")
        return False


def test_user_has_subscription():
    """Test 6: User now has subscription to server"""
    print("\n=== TEST 6: User Has Subscription ===")
    
    response = requests.get(
        f"{BASE_URL}/api/servers/my-subscriptions",
        headers=get_headers(USER_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        servers = response.json().get("servers", [])
        print(f"✓ User subscribed to {len(servers)} server(s)")
        return len(servers) > 0
    else:
        print("✗ Failed to fetch subscriptions")
        return False


def test_admin_rejects_duplicate_request():
    """Test 7: Admin rejects a duplicate request"""
    print("\n=== TEST 7: Admin Rejects Duplicate Request ===")
    
    # Create another request
    response = requests.post(
        f"{BASE_URL}/api/servers/requests",
        json={"server_id": SERVER_ID},
        headers=get_headers(USER_TOKEN)
    )
    
    if response.status_code != 200:
        print(f"✓ Correctly prevented duplicate request (Status: {response.status_code})")
        print(f"  Message: {response.json().get('detail', 'N/A')}")
        return True
    else:
        request_id = response.json().get("id")
        
        # Reject it
        response = requests.put(
            f"{BASE_URL}/api/servers/admin/requests/{request_id}/reject",
            json={"reason": "You already have access to this server"},
            headers=get_headers(ADMIN_TOKEN)
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(f"✓ Request rejected")
            return True
        else:
            print("✗ Failed to reject request")
            return False


def test_admin_sets_price():
    """Test 8: Admin sets server price"""
    print("\n=== TEST 8: Admin Sets Server Price ===")
    
    response = requests.put(
        f"{BASE_URL}/api/servers/admin/servers/{SERVER_ID}/price",
        json={"price_per_hour": 5.99},
        headers=get_headers(ADMIN_TOKEN)
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print(f"✓ Price set to ${response.json().get('price_per_hour')}/hour")
        return True
    else:
        print("✗ Failed to set price")
        return False


def run_all_tests():
    """Run all tests"""
    global USER_TOKEN, ADMIN_TOKEN, USER_ID, ADMIN_ID, SERVER_ID
    
    print("=" * 60)
    print("SUBSCRIPTION REQUEST WORKFLOW TEST")
    print("=" * 60)
    
    # Setup: Register/login test users
    print("\n=== SETUP ===")
    
    # Register user
    USER_TOKEN, USER_ID = register_and_login_user(
        "testuser@example.com",
        "testpass123",
        "testuser"
    )
    print(f"✓ User logged in: ID={USER_ID}, Token={USER_TOKEN[:20]}...")
    
    # Register admin
    ADMIN_TOKEN, ADMIN_ID = register_and_login_user(
        "admin@example.com",
        "adminpass123",
        "testadmin"
    )
    print(f"✓ Admin logged in: ID={ADMIN_ID}, Token={ADMIN_TOKEN[:20]}...")
    
    # Approve admin user
    response = requests.post(
        f"{BASE_URL}/api/admin/users/{ADMIN_ID}/approve",
        headers=get_headers(ADMIN_TOKEN)
    )
    print(f"Admin approved: {response.status_code}")
    
    # Get available servers
    response = requests.get(f"{BASE_URL}/api/servers")
    servers = response.json().get("servers", [])
    if servers:
        SERVER_ID = servers[0]["id"]
        print(f"✓ Using server: {servers[0]['name']} (ID={SERVER_ID})")
    else:
        print("✗ No servers available. Create servers first.")
        return
    
    # Run tests
    tests = [
        test_user_creates_request,
        test_user_views_requests,
        test_admin_views_pending_requests,
        test_admin_approves_request,
        test_user_sees_approved_status,
        test_user_has_subscription,
        test_admin_rejects_duplicate_request,
        test_admin_sets_price,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"✗ Test error: {e}")
            results.append((test.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    run_all_tests()
