# Server Subscription Request System

## Overview

This document describes the new server subscription request workflow implemented in the system. Instead of directly subscribing to servers, users now submit requests that admins must approve.

## System Architecture

### Database Model

**ServerSubscriptionRequest** (New Model)
- `id` - Primary key
- `user_id` - User requesting access (Foreign Key)
- `server_id` - Server being requested (Foreign Key)
- `status` - Request status: "pending", "approved", or "rejected"
- `requested_at` - Timestamp when request was created (Vietnam TZ)
- `approved_by` - Admin ID who approved (nullable)
- `approved_at` - Timestamp of approval (nullable)
- `rejection_reason` - Why request was rejected (nullable)

## API Endpoints

### User Endpoints

#### 1. Create Subscription Request
```
POST /api/servers/requests
Headers: Authorization: Bearer <token>
Body: { "server_id": <int> }

Response: 
{
  "id": 1,
  "user_id": 5,
  "server_id": 3,
  "status": "pending",
  "requested_at": "2025-01-15T10:30:00+07:00"
}
```

**Behavior:**
- Creates a new subscription request with status "pending"
- Returns error if user already has a pending/approved request for this server
- Validates that server exists

#### 2. Get User's Requests
```
GET /api/servers/requests
Headers: Authorization: Bearer <token>

Response:
{
  "requests": [
    {
      "id": 1,
      "server_id": 3,
      "server_name": "Web Server 1",
      "status": "pending",
      "requested_at": "2025-01-15T10:30:00+07:00",
      "approved_at": null,
      "rejection_reason": null
    },
    ...
  ],
  "total": 2
}
```

**Behavior:**
- Returns all requests for current user
- Sorted by most recent first
- Shows pending, approved, and rejected requests

### Admin Endpoints

#### 1. Get Pending Requests
```
GET /api/servers/admin/requests/pending
Headers: Authorization: Bearer <token> (Admin only)

Response:
{
  "requests": [
    {
      "id": 1,
      "user_id": 5,
      "user_email": "user@example.com",
      "user_name": "John Doe",
      "server_id": 3,
      "server_name": "Web Server 1",
      "server_specs": "2 CPU, 4GB RAM",
      "status": "pending",
      "requested_at": "2025-01-15T10:30:00+07:00"
    },
    ...
  ],
  "total": 3
}
```

**Behavior:**
- Only shows requests with status "pending"
- Ordered by most recent first
- Admin-only endpoint

#### 2. Approve Request
```
PUT /api/servers/admin/requests/{request_id}/approve
Headers: Authorization: Bearer <token> (Admin only)

Response:
{
  "id": 1,
  "status": "approved",
  "approved_at": "2025-01-15T11:00:00+07:00",
  "message": "Request approved and subscription created"
}
```

**Behavior:**
- Changes status to "approved"
- Records admin ID and approval timestamp
- **Automatically creates a ServerSubscription entry**
- User immediately gains access to the server

#### 3. Reject Request
```
PUT /api/servers/admin/requests/{request_id}/reject
Headers: Authorization: Bearer <token> (Admin only)
Body: { "reason": "Server capacity full" }

Response:
{
  "id": 1,
  "status": "rejected",
  "rejection_reason": "Server capacity full",
  "message": "Request rejected"
}
```

**Behavior:**
- Changes status to "rejected"
- Records rejection reason
- User can see why their request was denied
- User can submit a new request later

#### 4. Set Server Price
```
PUT /api/servers/admin/servers/{server_id}/price
Headers: Authorization: Bearer <token> (Admin only)
Body: { "price_per_hour": 5.99 }

Response:
{
  "id": 3,
  "name": "Web Server 1",
  "price_per_hour": 5.99,
  "message": "Price updated successfully"
}
```

**Behavior:**
- Updates the hourly price for a server
- Only admins can set prices
- Price is displayed to users when browsing servers

## Frontend Components

### ServerStore.jsx Updates

**New State:**
- `userRequests` - Array of user's subscription requests
- `requestsLoading` - Loading state for requests

**New Functions:**
- `fetchUserRequests()` - Load user's requests from API
- `handleRequestSubscription()` - Create new request instead of direct subscribe
- `getRequestStatus()` - Check request status for a server

**UI Changes:**
- "Subscribe to Monitor" button changes based on request status:
  - `idle` - Shows "Request Subscription"
  - `pending` - Shows "Request Pending" (disabled)
  - `approved` - Shows "Approved" or subscription status
  - `rejected` - Shows "Resubmit Request"
  
- Request rejection reasons are displayed with red highlighting
- New "Your Subscription Requests" section below subscriptions
  - Shows all pending, approved, and rejected requests
  - Displays approval/rejection timestamps
  - Shows rejection reasons if applicable

### AdminPanel.jsx Updates

**New Tab: "Server Requests"**

Features:
- View all pending subscription requests
- For each request, shows:
  - User email and name
  - Requested server name and specs
  - Request timestamp
  - Pending status badge

- Two action buttons per request:
  - **Approve** - Approves request and creates subscription
  - **Reject** - Rejects with optional reason (prompted)

- Shows loading states during processing
- Auto-refreshes after approve/reject

## User Experience Flow

### User Perspective

1. **Browse Servers**
   - User views available servers in ServerStore
   - See prices and specs for each server
   - Click "Request Subscription" button

2. **Submit Request**
   - Request is sent to admin
   - User sees button change to "Request Pending"
   - Request appears in "Your Subscription Requests" section

3. **Wait for Approval**
   - User monitors their requests
   - Can see if request is still pending
   - Can resubmit if rejected
   - Rejection reason is displayed if applicable

4. **Approved Status**
   - Button shows "Approved" when admin approves
   - Subscription appears in "Your Active Subscriptions"
   - User can now monitor the server metrics
   - Server metrics are automatically loaded

5. **Rejected Status**
   - Button shows "Resubmit Request" if rejected
   - Rejection reason is displayed
   - User can submit new request if desired

### Admin Perspective

1. **Review Requests**
   - Go to AdminPanel → "Server Requests" tab
   - See all pending requests with user and server info
   - Tab badge shows count of pending requests

2. **Approve Request**
   - Click "Approve" button for desired request
   - System automatically creates subscription
   - User immediately gains access
   - Button shows confirmation with timestamp

3. **Reject Request**
   - Click "Reject" button
   - Optional modal prompts for rejection reason
   - Reason is saved and shown to user
   - Request is removed from pending list

4. **Manage Pricing**
   - Through ServerStore or dedicated admin API
   - Set hourly price per server
   - Prices displayed to users

## Backend Implementation

### CRUD Functions (crud.py)

```python
def create_subscription_request(db, user_id, server_id)
  # Creates pending request, checks for duplicates
  
def get_pending_subscription_requests(db)
  # Gets all pending requests sorted by date
  
def approve_subscription_request(db, request_id, admin_id)
  # Approves request, auto-creates subscription
  
def reject_subscription_request(db, request_id, reason)
  # Rejects request with optional reason
  
def get_user_subscription_requests(db, user_id)
  # Gets all user's requests (pending/approved/rejected)
```

### API Routes (routes_servers.py)

Located under `/api/servers` prefix:

**User Routes:**
- `POST /requests` - Create new request
- `GET /requests` - View user's requests

**Admin Routes:**
- `GET /admin/requests/pending` - View pending requests
- `PUT /admin/requests/{id}/approve` - Approve request
- `PUT /admin/requests/{id}/reject` - Reject request
- `PUT /admin/servers/{id}/price` - Set server price

## Testing the System

### Manual Testing Steps

1. **Setup Test Servers**
   ```bash
   # Create servers using admin API
   curl -X POST http://localhost:8000/api/servers/admin/servers \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Server",
       "specs": "4 CPU, 8GB RAM",
       "cpu_cores": 4,
       "ram_gb": 8,
       "os_type": "Ubuntu",
       "price_per_hour": 0.0
     }'
   ```

2. **User Requests Subscription**
   ```bash
   curl -X POST http://localhost:8000/api/servers/requests \
     -H "Authorization: Bearer <user_token>" \
     -H "Content-Type: application/json" \
     -d '{"server_id": 1}'
   ```

3. **Admin Approves**
   ```bash
   curl -X PUT http://localhost:8000/api/servers/admin/requests/1/approve \
     -H "Authorization: Bearer <admin_token>"
   ```

4. **Verify Subscription**
   ```bash
   curl -X GET http://localhost:8000/api/servers/my-subscriptions \
     -H "Authorization: Bearer <user_token>"
   ```

### Automated Testing

Run the test script:
```bash
python test_subscription_requests.py
```

This tests:
- User creates request
- User views their requests  
- Admin views pending requests
- Admin approves request
- Subscription is automatically created
- Admin rejects duplicate attempts
- Price can be set

## Key Features

✅ **Request Tracking** - Full lifecycle from pending to approved/rejected
✅ **Admin Authorization** - Only admins can approve/reject/set prices
✅ **Automatic Subscription** - Approval immediately creates subscription
✅ **Reason Logging** - Rejection reasons help users understand decisions
✅ **Duplicate Prevention** - Users can't spam multiple requests
✅ **Real-time Status** - UI updates reflect request status immediately
✅ **Vietnam Timezone** - All timestamps use UTC+7
✅ **Error Handling** - Clear error messages for all edge cases

## Future Enhancements

- Email notifications when request approval status changes
- Request expiration after certain period
- Admin dashboard with request analytics
- Bulk action buttons for approving multiple requests
- Request templates for rejection reasons
- Server capacity limits enforcement
- Monthly usage tracking and limits

