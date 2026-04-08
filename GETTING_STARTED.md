# 🚀 Getting Started - Hướng Dẫn Bắt Đầu

Hướng dẫn này sẽ giúp bạn chạy hệ thống **Real-Time Metrics Processing and Server Management** từ đầu.

---

## 📋 Yêu cầu trước khi bắt đầu

- **Python 3.8+** (khuyến nghị 3.10+)
- **Node.js 16+** và npm
- **Git** (tùy chọn)

---

## 🛠️ Cài đặt Backend

### Bước 1: Tạo Virtual Environment

```bash
cd d:\DuLieuCuaHuu\HK2_20252026\PTUD\CK\CK2\test_CK_PTUD-main

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 2: Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

Các dependencies chính:
- **FastAPI**: Framework web hiện đại
- **SQLAlchemy**: ORM cho database
- **psutil**: Thu thập metrics hệ thống
- **python-jose**: JWT authentication

### Bước 3: Khởi tạo Database

```bash
python migrate_db.py
```

---

## ⚡ Chạy hệ thống

### Terminal 1: Chạy Backend Server

```bash
python app/main.py
```

Hoặc sử dụng `uvicorn`:

```bash
uvicorn app.main:app --reload --port 8000
```

✅ Backend sẽ chạy tại: **http://localhost:8000**

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔐 Đăng nhập hệ thống

### Tài khoản mặc định

#### Admin Account
- **Email**: `admin@example.com`
- **Password**: `admin123`
- **Role**: Administrator

#### User Account
- **Email**: `user@example.com`
- **Password**: `user123`
- **Role**: Regular User

### Đăng ký tài khoản mới

1. Truy cập trang **Login**
2. Nhấp **"Don't have an account? Sign up"**
3. Điền thông tin (Email, Password, Name)
4. Nhấn **Sign Up**

---

## 📊 Hướng dẫn sử dụng chính

### 👨‍💼 Admin View

**Đăng nhập với tài khoản Admin**, bạn có thể:

1. **Quản lý Servers**
   - Xem danh sách tất cả servers
   - Edit tên, specifications, giá hằng tháng
   - Xem system info (CPU cores, RAM, OS type)
   - Xem biểu đồ metrics (CPU, Memory) - 2 giờ gần nhất
   - Quản lý các yêu cầu subscribe từ users

2. **Xem Chart Metrics**
   - Nhấp vào bất kỳ server card nào
   - Xem biểu đồ CPU và Memory của 2 giờ gần đây
   - Xem thống kê trung bình, min, max

3. **Quản lý Requests**
   - Xem yêu cầu subscribe từ users
   - Approve hoặc Reject requests

4. **Quản lý Users**
   - Xem danh sách tất cả users
   - Quản lý thông tin users

### 👤 User View

**Đăng nhập với tài khoản User**, bạn có thể:

1. **Browse Available Servers**
   - Xem danh sách servers có sẵn
   - Xem giá hằng tháng, CPU, RAM, OS

2. **Subscribe to Server**
   - Nhấp "Request" trên server card
   - Chờ admin approve

3. **My Subscriptions**
   - Xem những servers đã subscribe
   - Xem chart metrics của những servers này

4. **Track Requests**
   - Xem trạng thái yêu cầu subscribe (Pending, Approved, Rejected)
   - Xem lý do reject (nếu có)

---

## 📁 Cấu trúc Project

```
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration
│   ├── database.py              # Database setup
│   ├── models.py                # SQLAlchemy models
│   ├── crud.py                  # Database operations
│   ├── schemas.py               # Data schemas
│   ├── system_metrics.py        # System metrics collector
│   ├── websocket_manager.py     # WebSocket handling
│   ├── api/
│   │   ├── routes_auth.py       # Authentication
│   │   ├── routes_servers.py    # Server management
│   │   ├── routes_metrics.py    # Metrics endpoints
│   │   ├── routes_alerts.py     # Alerts
│   │   ├── routes_admin.py      # Admin features
│   │   └── routes_websocket.py  # WebSocket API
│   └── services/
│       └── metrics_service.py   # Business logic
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # Entry point
│   │   ├── App.jsx              # Main component
│   │   ├── api.js               # API client
│   │   ├── index.css            # Global styles
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ServerStore.jsx  # Main server UI
│   │   │   ├── AdminPanel.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── ...
│   │   └── context/
│   │       ├── AuthContext.jsx  # Auth state
│   │       └── DeviceContext.jsx # Device state
│   └── package.json
│
├── GETTING_STARTED.md           # This file
├── QUICK_START.md               # Quick start guide
├── README.md                    # Project overview
├── requirements.txt             # Python packages
└── metrics.db                   # SQLite database
```

---

## 🔧 Các lệnh tiện ích

### Backend Commands

```bash
# Chạy backend với auto-reload
python app/main.py

# Hoặc sử dụng uvicorn
uvicorn app.main:app --reload --port 8000

# Chạy trên port khác
uvicorn app.main:app --port 8001

# Kiểm tra database
python check_db.py

# Dọn dẹp devices
python cleanup_devices.py

# Migrate database
python migrate_db.py
```

### Frontend Commands

```bash
# Chạy development server
npm run dev

# Build cho production
npm run build

# Preview production build
npm run preview
```

### Utility Scripts

```bash
# Thu thập system metrics
python collect_system_metrics.py

# Tạo IoT data
python generate_iot_data.py --continuous --interval 2

# Chạy full test
python full_test.py

# Dừng với Ctrl+C
```

---

## 📡 API Endpoints chính

### Authentication
```
POST   /api/auth/register          - Đăng ký tài khoản
POST   /api/auth/login             - Đăng nhập
GET    /api/auth/me                - Lấy thông tin user hiện tại
```

### Servers (Admin)
```
GET    /api/servers/admin/servers          - Lấy tất cả servers
POST   /api/servers/admin/servers          - Tạo server mới
PUT    /api/servers/admin/servers/{id}     - Edit server (name, specs, price)
DELETE /api/servers/admin/servers/{id}     - Xóa server
GET    /api/servers/admin/system-info      - Lấy system info (CPU, RAM, OS)
```

### Servers (User)
```
GET    /api/servers                        - Lấy danh sách servers khả dụng
POST   /api/servers/{id}/subscribe         - Subscribe server
DELETE /api/servers/{id}/unsubscribe       - Unsubscribe
GET    /api/servers/my-subscriptions       - Lấy subscriptions của user
```

### Subscription Requests
```
POST   /api/servers/requests                              - Tạo yêu cầu subscribe
GET    /api/servers/requests                              - Xem yêu cầu của user
GET    /api/servers/admin/requests/pending                - Admin xem yêu cầu chờ
PUT    /api/servers/admin/requests/{id}/approve           - Admin approve
PUT    /api/servers/admin/requests/{id}/reject            - Admin reject
```

### Metrics
```
GET    /api/metrics/latest                 - Metrics mới nhất của localhost
GET    /api/metrics/history                - Lịch sử metrics (CPU/Memory)
```

---

## � Troubleshooting

### ❌ Backend không kết nối được

**Triệu chứng**: Frontend hiển thị "Failed to connect to server"

**Giải pháp**:
1. Kiểm tra backend đang chạy tại `http://localhost:8000`
2. Kiểm tra `frontend/src/api.js` có config đúng base URL
3. Chạy lại: `python app/main.py`

### ❌ Database bị lỗi

**Triệu chứng**: Lỗi "No such table" hoặc "Database error"

**Giải pháp**:
```bash
# Xóa database cũ (nếu cần)
rm app.db

# Tạo database mới
python migrate_db.py
```

### ❌ Metrics không hiển thị

**Triệu chứng**: Biểu đồ trống hoặc không có dữ liệu

**Giải pháp**:
1. Backend cần chạy ít nhất 1-2 phút để thu thập metrics
2. Chạy thủ công: `python collect_system_metrics.py`
3. Kiểm tra endpoint `/api/metrics/latest`

### ❌ Port 8000 hoặc 5173 bị chiếm dụng

**Giải pháp**:
```bash
# Chạy backend trên port khác
uvicorn app.main:app --reload --port 8001

# Chạy frontend trên port khác
npm run dev -- --port 5174
```

### ❌ Frontend hiển thị lỗi 404 khi Edit Server

**Triệu chứng**: "Error: Server not found" khi nhấp Save trong Edit modal

**Giải pháp**:
1. Backend cần restart để load endpoint mới: `python app/main.py`
2. Kiểm tra browser console (F12) để xem chi tiết lỗi
3. Đảm bảo đã run migration: `python migrate_db.py`

---

## 📊 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│        Frontend (React + Vite)                      │
│       http://localhost:5173                         │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ ServerStore  │ Admin Panel  │ Login        │    │
│  │ + Charts     │ + Dashboard  │ + Sidebar    │    │
│  └──────────────┴──────────────┴──────────────┘    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
                     ↓
┌─────────────────────────────────────────────────────┐
│        Backend (FastAPI)                            │
│       http://localhost:8000                         │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ Auth Routes  │ Server Routes│ Metrics API  │    │
│  │              │ Request Mgmt │ Admin Routes │    │
│  └──────────────┴──────────────┴──────────────┘    │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
          ┌──────────────────────┐
          │  SQLite Database     │
          │  (metrics.db)        │
          │                      │
          │ Tables:              │
          │ - Users              │
          │ - AvailableServers   │
          │ - ServerSubscriptions│
          │ - Requests           │
          │ - Metrics            │
          └──────────────────────┘
```

---

## 🎯 Các bước tiếp theo

1. **Đăng nhập hệ thống**: Sử dụng tài khoản Admin hoặc User
2. **Khám phá Admin View**: Xem danh sách servers và quản lý chúng
3. **Edit Server**: Thay đổi tên, specs, hoặc giá hằng tháng
4. **Xem Metrics**: Click vào server card để xem biểu đồ CPU/Memory
5. **Quản lý Requests**: Approve hoặc Reject các yêu cầu subscribe từ users

---

## 📚 Tài liệu tham khảo

- **FastAPI Docs**: http://localhost:8000/docs (Swagger UI)
- **API Schema**: http://localhost:8000/openapi.json
- **Frontend Logs**: Browser Console (F12)
- **Backend Logs**: Terminal output
- **QUICK_START.md**: Hướng dẫn bắt đầu nhanh
- **README.md**: Thông tin chi tiết về dự án

---

## ❓ Cần trợ giúp?

1. Kiểm tra browser console (F12) để xem lỗi frontend
2. Kiểm tra terminal output để xem lỗi backend
3. Xem `README.md` để hiểu tổng quan dự án
4. Xem `IMPLEMENTATION_SUMMARY.md` để xem các tính năng đã implement
5. Xem các file guides khác (WEBSOCKET_GUIDE.md, CLIENT_MONITOR_GUIDE.md, etc.)

---

**Chúc bạn sử dụng hệ thống vui vẻ! 🎉**
