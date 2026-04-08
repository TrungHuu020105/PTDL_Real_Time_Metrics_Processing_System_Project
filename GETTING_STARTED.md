# 🚀 Getting Started - MetricsPulse v2.0

Hướng dẫn bắt đầu nhanh cho hệ thống giám sát IoT và Server toàn diện.

---

## 📋 Prerequisites

- **Python 3.9+** - Backend
- **Node.js 16+** & **npm** - Frontend
- **Git** - Version control

---

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd test_CK_PTUD-main
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## ⚡ Quick Start (5 minutes)

### Terminal 1️⃣: Start Backend Server
```bash
python -m uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Started server process
Uvicorn running on http://127.0.0.1:8000
```

✅ Backend ready at: **http://localhost:8000**

---

### Terminal 2️⃣: Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.0.12  ready in 123 ms

➜ Local: http://localhost:3000/
```

✅ Frontend ready at: **http://localhost:3000**

---

### Terminal 3️⃣: Start System Metrics Collector
```bash
python collect_system_metrics.py
```

This collects CPU and Memory metrics every 2 seconds from localhost.

---

### Terminal 4️⃣: Start IoT Data Generator
```bash
python generate_iot_data.py --continuous --interval 2
```

This generates random sensor data (temperature, humidity, soil moisture, light, pressure) every 2 seconds.

---

## 🔐 First Login

1. Open **http://localhost:3000** in your browser
2. Create an account or use test credentials
3. Admin account (if available):
   - Username: `admin`
   - Password: `admin123` (if default exists)

---

## 📊 Features Overview

### 👤 Regular Users Can:
- ✅ View their IoT devices with **real-time metrics**
- ✅ Click devices to see **2-hour historical charts**
- ✅ View alerts
- ✅ Browse and manage rented servers

### 🔧 Admin Users Can:
- ✅ Access Dashboard with system metrics
- ✅ **Manage all user IoT devices** (view, delete, disconnect/reconnect)
- ✅ See device ownership with usernames
- ✅ Manage user accounts (approve, reject, delete)
- ✅ Create and manage server offerings
- ✅ View admin panel

---

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy ORM models
│   ├── crud.py              # Database operations
│   ├── schemas.py           # Pydantic schemas
│   ├── config.py            # Configuration
│   ├── api/
│   │   ├── routes_auth.py       # Authentication endpoints
│   │   ├── routes_metrics.py    # Metrics endpoints
│   │   ├── routes_alerts.py     # Alerts endpoints
│   │   ├── routes_admin.py      # Admin endpoints
│   │   └── routes_websocket.py  # WebSocket endpoints
│   └── services/
│       └── metrics_service.py   # Business logic
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── api.js               # API client (axios)
│   │   ├── components/
│   │   │   ├── IoTDeviceManager.jsx     # Device management with charts
│   │   │   ├── AdminDashboard.jsx       # Admin dashboard
│   │   │   ├── AdminPanel.jsx           # Admin user management
│   │   │   ├── Dashboard.jsx            # User dashboard
│   │   │   ├── Sidebar.jsx              # Navigation sidebar
│   │   │   ├── Alerts.jsx               # Alerts display
│   │   │   └── ...
│   │   └── context/
│   │       ├── AuthContext.jsx          # Auth state management
│   │       └── DeviceContext.jsx        # Device state management
│   └── package.json
│
├── collect_system_metrics.py    # System metrics collector
├── generate_iot_data.py          # IoT data simulator
├── requirements.txt              # Python dependencies
└── README.md

```

---

## 🔧 Common Commands

### Backend

```bash
# Run with auto-reload (development)
python -m uvicorn app.main:app --reload

# Run on specific port
python -m uvicorn app.main:app --port 8001

# Check database
python check_db.py

# Fix IoT sources
python fix_iot_sources.py

# Cleanup devices
python cleanup_devices.py

# Migrate database
python migrate_db.py
```

### Frontend

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Data Collection

```bash
# System metrics (CPU, Memory)
python collect_system_metrics.py

# IoT sensor data (Temperature, Humidity, etc.)
python generate_iot_data.py --continuous --interval 2

# Stop with Ctrl+C
```

---

## 📡 API Endpoints

### Public Endpoints
```
POST   /api/auth/register              # Register new user
POST   /api/auth/login                 # Login
POST   /api/auth/refresh               # Refresh token
```

### User Endpoints (Protected)
```
GET    /api/iot-devices                # Get user's IoT devices
POST   /api/iot-devices                # Create new IoT device
PUT    /api/iot-devices/{id}           # Update IoT device
DELETE /api/iot-devices/{id}           # Delete IoT device

GET    /api/metrics/latest             # Get latest metrics
GET    /api/metrics/history            # Get historical metrics (supports query params)
GET    /api/metrics/summary            # Get metrics summary

GET    /api/servers                    # Get available servers
GET    /api/servers/my-subscriptions   # Get user's servers
POST   /api/servers/{id}/subscribe     # Subscribe to server
DELETE /api/servers/{id}/unsubscribe   # Unsubscribe from server

GET    /api/alerts                     # Get user's alerts
```

### Admin Endpoints (Protected)
```
GET    /api/admin/users                # List all users
GET    /api/admin/users/pending        # List pending users
POST   /api/admin/users/{id}/approve   # Approve user
POST   /api/admin/users/{id}/reject    # Reject user
DELETE /api/admin/users/{id}           # Delete user

GET    /api/admin/iot-devices          # List all IoT devices
DELETE /api/admin/iot-devices/{id}     # Delete device
PUT    /api/admin/iot-devices/{id}/disconnect    # Deactivate device
PUT    /api/admin/iot-devices/{id}/reconnect    # Reactivate device

GET    /api/admin/servers              # Manage server offerings
```

---

## 🔍 Troubleshooting

### Frontend won't start
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend errors
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check database
python check_db.py
```

### Port already in use
```bash
# Frontend on different port
cd frontend
npm run dev -- --port 3001

# Backend on different port
python -m uvicorn app.main:app --port 8001
```

### Database connection error
```bash
# Reset database
python migrate_db.py

# Check database file exists
ls -la *.db  # On Linux/Mac
dir *.db     # On Windows
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           Frontend (React + Vite)                   │
│        http://localhost:3000                        │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ IoT Devices  │ Admin Panel  │ Alerts       │    │
│  │ + Charts     │ + Dashboard  │ + Servers    │    │
│  └──────────────┴──────────────┴──────────────┘    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/WebSocket
                     ↓
┌─────────────────────────────────────────────────────┐
│         Backend (FastAPI)                           │
│        http://localhost:8000                        │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ Auth Routes  │ Metrics API  │ Admin Routes │    │
│  │              │ WebSocket    │ Server Mgmt  │    │
│  └──────────────┴──────────────┴──────────────┘    │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
          ┌──────────────────────┐
          │  SQLite Database     │
          │  (metrics.db)        │
          └──────────────────────┘
```

---

## 🎯 Next Steps

1. **Explore the Dashboard**: After login, check your IoT devices
2. **Create an IoT Device**: Try creating a test device in the UI
3. **View Charts**: Click a device to see 2-hour historical data
4. **Admin Features** (if admin):
   - Check Admin Dashboard
   - View all user devices
   - Manage user accounts in Admin Panel
5. **Set Up Alerts**: Configure alert thresholds for your devices

---

## 📚 Resources

- **FastAPI Docs**: http://localhost:8000/docs (Swagger UI)
- **API Schema**: http://localhost:8000/openapi.json
- **Frontend Logs**: Browser Console (F12)
- **Backend Logs**: Terminal output

---

## ❓ Need Help?

1. Check browser console (F12) for frontend errors
2. Check terminal output for backend errors
3. See `IMPLEMENTATION_SUMMARY.md` for detailed features
4. See `README_WEBSOCKET.md` for WebSocket setup
5. See `CLIENT_MONITOR_GUIDE.md` for monitoring setup

---

**Happy Monitoring! 🎉**
