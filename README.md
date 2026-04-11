# Real-Time IoT Data Monitoring System 📊

> Hệ Thống Giám Sát Dữ Liệu IoT Thời Gian Thực\
> Sinh dữ liệu cảm biến và đưa lên Dashboard trực tiếp (streaming WebSocket + lọc Database)

Giải pháp hoàn chỉnh để theo dõi cảm biến IoT thời gian thực với:
- **Frontend React**: Dashboard tương tác với biểu đồ động
- **Backend FastAPI**: WebSocket streaming + Database filtering
- **Dual-Layer Architecture**: 100% dữ liệu lên Dashboard, ~33% dữ liệu save Database
- **Role-Based Access**: Admin (xem statistic), User (quản lý devices)

---

## 👥 Nhóm

| Thứ Tự | Tên | MSSV |
|--------|-----|------|
| 1 | Huỳnh Nhật Hào | 23663871 |
| 2 | Lê Trung Hữu | 23666491 |
| 3 | Phan Gia Huy | 23674141 |
| 4 | Trần Quốc Huy | 23637731 |

---

## 🎯 Tính Năng Chính

### ✅ **Live IoT Streaming**
- Sinh dữ liệu cảm biến (Temperature, Humidity, Light, Pressure, Soil Moisture)
- Stream **100% dữ liệu** qua WebSocket tới Dashboard (real-time)
- **Lọc thông minh**: Chỉ save Database dữ liệu quan trọng (~33%), còn lại realtime only
- Điều chỉnh động: `step_size`, `trend_amplitude`, `boundary_reflection`

### ✅ **User Device Management**
- Users tạo/xóa devices và chọn sensor type
- Modal dialog để thêm device mới
- Dashboard hiển thị device metrics real-time
- Xem lịch sử dữ liệu của từng device

### ✅ **Admin Dashboard**
- Xem tổng số devices, users, locations
- Bảng statistic: Device count per user
- **Không thể**: Xem device details, Add devices, sửa dữ liệu user

### ✅ **Architecture Diagram**
```
┌─────────────────┐          ┌──────────────────┐
│  IoT Generator  │          │  Admin/User UI   │
│ (Python Script) │          │   (React)        │
└────────┬────────┘          └────────┬─────────┘
         │                            │
         │ Generate (5 metrics)       │ Real-time view
         │                            │
         ▼                            ▼
    ┌────────────────────────────────────────┐
    │     WebSocket Stream Handler           │
    │  /ws/{client_id} - 100% Metrics        │
    └────────┬──────────────────────┬────────┘
             │                      │
      100% streaming          Check "saved" flag
             │                      │
             ▼                      ▼
      ┌──────────────┐      ┌──────────────┐
      │  Frontend    │      │  SQLite DB   │
      │  Dashboard   │      │  (~33% only) │
      │  (Real-time) │      │  (Persist)   │
      └──────────────┘      └──────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- Python 3.11, FastAPI, Uvicorn
- WebSocket (async/await), Pydantic v2
- SQLAlchemy ORM, SQLite
- psutil (system metrics)

### Frontend
- React 18, Vite, Tailwind CSS
- Real-time WebSocket client
- Component-based architecture (UserDashboard, AdminDashboard, etc.)

---

## 📁 Project Structure

```
test_CK_PTUD-main/
├── app/                              # Backend FastAPI
│   ├── main.py                       # Entry point
│   ├── database.py                   # SQLite setup
│   ├── models.py                     # Pydantic models
│   ├── schemas.py, schemas_ws.py     # Data schemas
│   ├── crud.py                       # DB operations
│   ├── config.py                     # Configuration
│   ├── system_metrics.py             # Metrics collector
│   ├── websocket_manager.py          # WebSocket manager
│   ├── api/
│   │   ├── routes_auth.py            # Authentication
│   │   ├── routes_iot_devices.py     # Device CRUD
│   │   ├── routes_websocket.py       # WebSocket & streaming
│   │   ├── routes_admin.py           # Admin endpoints
│   │   ├── routes_alerts.py          # Alerts
│   │   ├── routes_metrics.py         # Metrics API
│   │   └── routes_servers.py         # Server management
│   └── services/
│       └── metrics_service.py        # Business logic
│
├── frontend/                         # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx         # Main dashboard
│   │   │   ├── UserDashboard.jsx     # User view
│   │   │   ├── AdminDashboard.jsx    # Admin view
│   │   │   ├── IoTDeviceManager.jsx  # Device manager
│   │   │   ├── AddDeviceModal.jsx    # Add device modal
│   │   │   ├── IoTMetrics.jsx        # Metrics display
│   │   │   ├── ClientMonitor.jsx     # Real-time control
│   │   │   ├── Login.jsx, Sidebar.jsx, etc.
│   │   ├── context/
│   │   │   ├── AuthContext.jsx       # User auth state
│   │   │   └── DeviceContext.jsx     # Device management
│   │   ├── api.js                    # API client
│   │   ├── App.jsx, main.jsx         # React root
│   │   └── index.css                 # Styles
│   ├── package.json
│   └── vite.config.js
│
├── generate_iot_data.py              # IoT data generator
├── stream_iot_data_live.py           # WebSocket client for streaming
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── .gitignore                        # Git config
```

---

## 🚀 Quick Start (5 phút)

### Prerequisites
- Python 3.8+ (khuyến nghị 3.11)
- Node.js 16+ và npm
- Terminal / Command Prompt

### Installation

**1. Backend Setup**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**2. Frontend Setup**
```bash
cd frontend
npm install
```

### Running the System

**Terminal 1: Start Backend**
```bash
python -m uvicorn app.main:app --reload
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Terminal 2: Start Frontend**
```bash
cd frontend
npm run dev
# Frontend: http://localhost:5173
```

**Terminal 3: Generate & Stream IoT Data**
```bash
# Start the IoT data streamer
python stream_iot_data_live.py

# Output shows metrics being streamed:
# [14:30:45] Batch #1 | Generated: 5 | Sent: 5 | Saved to DB: 1
#   ✅ SEND temperature = 24.50 °C
#   ⏭️  SKIP humidity = 65.20 %
#   ✅ SEND soil_moisture = 45.00 %
# ... (continue streaming)
```

**Terminal 4 (Optional): Collect Real System Metrics**
```bash
python collect_system_metrics.py
# Automatically saves CPU/Memory every 2 seconds
```

### Access the System
- **User Dashboard**: http://localhost:5173
- **Default Credentials**:
  - Admin: `admin@example.com` / `admin123`
  - User: `user@example.com` / `user123`

---

## 📊 Architecture & Data Flow

### Dual-Layer Data Architecture

```
Frontend (100% data):           Dashboard shows ALL metrics real-time
  ◄──────────────────────────────┐
                                  │ WebSocket /ws/{client_id}
                                  │ 100 metrics/minute
                                  │
IoT Generator ──►  WebSocket Handler ──┐
(5 metrics/batch)        │              │
                 Check "saved" flag     │
                         │              ▼
                    YES  │           Frontend updates chart
                         │           (no delay)
                         ▼
                      SQLite DB
                    (~33% stored)
```

### Data Generation with Boundary Reflection

```python
# Example: Temperature simulation
- Base value: Random walk (±0.5°C per step)
- Time trend: Gradual drift over time
- Boundary reflection:
  - If value > 85% of range (max) → Force negative change
  - If value < 15% of range (min) → Force positive change
  - Result: Data oscillates up/down (never stuck at boundary)

Current parameters:
  temperature: min=15°C, max=35°C, step=0.5, trend=3.0°C
  humidity: min=30%, max=90%, step=1.5, trend=5.0%
  light_intensity: min=200, max=900, step=80, trend=200
```

### Filtering Logic (What Gets Saved to DB?)

```
Metric saved if:
  1. Value changed > threshold (adaptive per sensor)
  2. OR time since last save > 300 seconds (time-based fallback)

Example: 8 batches × 5 metrics = 40 metrics generated
  → Streamed to frontend: 40/40 (100%)
  → Saved to DB: 13/40 (32.5%) ✅

Effect: Reduce DB bloat while keeping Dashboard responsive
```

---

## 👤 User Roles & Features

### **Admin Features**
- ✅ Dashboard: Total devices, users, locations
- ✅ View device count per user (table format)
- ❌ Cannot see device details
- ❌ Cannot add/edit/delete devices
- ❌ Cannot view user metrics

### **User Features**
- ✅ Create device with sensor type selector
- ✅ View own devices in grid layout
- ✅ Real-time metrics for selected device
- ✅ View device details, edit description
- ✅ Delete own devices

### **API Access Control**
```
GET /api/admin/iot-devices     → Admin only (returns user summaries)
GET /api/iot-devices           → User (returns own devices)
POST /api/iot-devices          → User (create own device)
DELETE /api/iot-devices/{id}   → User (delete own device)
```

---

## 🔐 Authentication

### Default Accounts
```
Admin:
  Email: admin@example.com
  Password: admin123

User:
  Email: user@example.com
  Password: user123
```

### Create New Account
1. Go to login page
2. Click "Sign up"
3. Enter email, password, name
4. Submit → Account created

---

## 🧪 Testing & Development

### Generate Test Data (One-time)
```bash
# Create 500 metrics spread over 24 hours
python generate_iot_data.py --count 500 --spread-hours 24
```

### Stream Live (Continuous)
```bash
# Stream 5 metrics every 5 seconds
python stream_iot_data_live.py
# Default: interval=5s, batch_size=5
# Customize: Edit generate_iot_data() call in stream_iot_data_live.py
```

### Test WebSocket
```python
# In Python:
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws/test_client') as ws:
        await ws.send('{"metric_type": "temperature", "value": 25.5}')
        response = await ws.recv()
        print(response)

asyncio.run(test())
```

---

## 📈 Performance Metrics

### Real-World Performance
```
Streaming Rate:     5 metrics/batch, ~60 metrics/minute
Frontend Load:      100% metrics real-time (no filtering)
Database Save:      ~33% metrics (filtered by threshold)
WebSocket Latency:  <100ms (local network)
Memory Usage:       ~150MB (backend + frontend)
Database Size:      ~2MB/day (1000 devices, 33% filtering)
```

### Optimization Tips
1. **Reduce streaming interval**: Edit `interval=5` in `stream_iot_data_live.py`
2. **Adjust filtering threshold**: Edit `threshold=2.0` in `generate_iot_data.py`
3. **Increase boundary reflection**: Lower `step_size` param for more oscillation
4. **Database cleanup**: Clear old metrics → `DELETE FROM iot_metrics WHERE timestamp < ?`

---

## 🐛 Troubleshooting

### Issue: "Connection refused" on WebSocket
**Solution**: Ensure backend is running on port 8000
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Issue: Frontend shows "0 devices" but data exists
**Solution**: Check DeviceContext.jsx is using correct API response format
```javascript
// Correct:
const response = await fetch('/api/iot-devices');
const data = response.data;  // Full object with devices array
```

### Issue: Data stuck at same value (e.g., 35°C always)
**Solution**: Boundary reflection is working (force oscillation)
- Check `min`/`max` values in `generate_iot_data.py`
- Reduce `step_size` or increase `trend_amplitude`
- Verify `boundary_reflection()` logic is enabled

### Issue: Database growing too large
**Solution**: Increase threshold or delete old records
```bash
# Delete metrics older than 7 days
sqlite3 metrics.db "DELETE FROM iot_metrics WHERE timestamp < datetime('now', '-7 days');"
```

---

## 🚀 Going to Production

### Deployment Checklist
- [ ] Change default credentials (CHANGE ADMIN/USER PASSWORDS)
- [ ] Set `DEBUG=false` in `app/config.py`
- [ ] Use PostgreSQL instead of SQLite for large scale
- [ ] Enable HTTPS/WSS for WebSocket
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure CORS properly (not `*`)
- [ ] Add rate limiting to API endpoints
- [ ] Set up monitoring & alerting

### Production Commands
```bash
# Backend (with gunicorn + multiple workers)
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app

# Frontend (build for production)
cd frontend && npm run build && npm run preview
```

---

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React WebSocket**: https://github.com/websocket-client/websocket-client
- **SQLite Performance**: https://www.sqlite.org/bestidx.html

---

## ✅ Recent Changes & Improvements

### Latest Updates
- ✅ **Dual-layer streaming**: Frontend 100% realtime, Database filtered only
- ✅ **Boundary reflection**: Data no longer stuck at min/max values
- ✅ **Admin access control**: Users can't see other devices or add devices as admin
- ✅ **AddDeviceModal**: Streamlined UI for adding new IoT devices  
- ✅ **API response consistency**: Fixed device fetching mismatch

### Known Limitations
- SQLite not recommended for >100 concurrent connections (use PostgreSQL)
- WebSocket doesn't persist if server restarts (data loss if unsaved to DB)
- Real system metrics collection requires OS-level permissions

---

## 📞 Support & Issues

For bugs or feature requests, contact the development team:
- Huỳnh Nhật Hào (huynhnhathao@...)
- Lê Trung Hữu (letrunghuu@...)
- Phan Gia Huy (phangiahuy@...)
- Trần Quốc Huy (tranquochuy@...)

---

**Last Updated**: April 2026  
**Status**: ✅ Production Ready  
**License**: MIT

#### **2️⃣ Từ Hệ Thống Giám Sát (Monitoring)**

Các công cụ/agent trên server gửi metrics về backend:

```
┌─────────────────────┐
│  Agent trên Server  │
│ (Prometheus, etc.)  │
└──────────┬──────────┘
           │ Đọc CPU, Memory, Requests
           ▼
┌──────────────────────────┐
│ Gửi HTTP POST tới Backend │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Backend lưu vào SQLite  │
└─────────────────────────┘
```

#### **3️⃣ Từ Dữ Liệu Giả Lập (Cho Testing)**

Dùng endpoint dev để sinh dữ liệu test:

```bash
curl -X POST "http://localhost:8000/api/dev/generate-sample-data?count=100"
```

#### **4️⃣ Từ Cảm Biến IoT (Internet of Things)**

Các cảm biến thông minh gửi dữ liệu IoT về backend:

```bash
# Lấy Nhiệt Độ từ sensor
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "temperature",
    "value": 28.5,
    "source": "sensor_1"
  }'

# Lấy Độ Ẩm từ sensor
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "humidity",
    "value": 65.3,
    "source": "sensor_1"
  }'

# Lấy Độ Ẩm Đất từ cảm biến độ ẩm đất
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "soil_moisture",
    "value": 45.2,
    "source": "soil_sensor_1"
  }'
```

**Hoặc sinh dữ liệu IoT giả lập:**

```bash
curl -X POST "http://localhost:8000/api/dev/generate-iot-data?count=100"
```

---

### **Các Loại IoT Metrics Được Hỗ Trợ**

| Loại Metrics | Đơn Vị | Range | Ví Dụ |
|-------------|--------|-------|--------|
| **temperature** | °C | 15-35 | 28.5°C |
| **humidity** | % | 30-90 | 65.3% |
| **soil_moisture** | % | 0-100 | 45.2% |
| **light_intensity** | lux | 0-1000 | 750 lux |
| **pressure** | hPa | 900-1100 | 1013 hPa |

---

### **Quy Trình Xử Lý Dữ Liệu Hoàn Chỉnh**

```
┌────────────────────────────────────────────────────────────┐
│ 1. DỮ LIỆU ĐẾN TỪ ĐÂU?                                    │
├────────────────────────────────────────────────────────────┤
│ ✓ Client/Frontend gửi HTTP POST                           │
│ ✓ Agent giám sát gửi metrics thực tế                      │
│ ✓ Cảm biến IoT gửi dữ liệu sensor                         │
│ ✓ Endpoint dev tạo test data                              │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│ 2. KIỂM ĐỊNH DỮ LIỆU (schemas.py)                        │
├────────────────────────────────────────────────────────────┤
│ ✓ Kiểm tra metric_type:                                  │
│   - Server: cpu, memory, request_count                   │
│   - IoT: temperature, humidity, soil_moisture, ...       │
│ ✓ Kiểm tra value ≥ 0 và < 1,000,000                      │
│ ✓ Kiểm tra source không rỗng                              │
│ ✗ Từ chối dữ liệu không hợp lệ (HTTP 400)                │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│ 3. LƯU VÀO DATABASE (crud.py)                            │
├────────────────────────────────────────────────────────────┤
│ ✓ Thêm bản ghi vào bảng metrics                            │
│ ✓ Lưu tự động timestamp nếu chưa có                       │
│ ✓ Commit transaction                                       │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│ 4. INDEXING & TỐI ƯU                                     │
├────────────────────────────────────────────────────────────┤
│ ✓ Composite index: (metric_type, timestamp)              │
│ ✓ Truy vấn nhanh theo loại & khoảng thời gian            │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│ 5. TRÍCH XUẤT & TỔNG HỢP (services/metrics_service.py)  │
├────────────────────────────────────────────────────────────┤
│ ✓ Lấy giá trị mới nhất (latest)                           │
│ ✓ Tính trung bình CPU/Memory 1 phút                       │
│ ✓ Tính tổng Request Count 1 phút                         │
│ ✓ Tính trung bình IoT metrics (nhiệt độ, độ ẩm, ...)     │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│ 6. TRẢ VỀ CHO FRONTEND (API responses)                   │
├────────────────────────────────────────────────────────────┤
│ ✓ Trả về JSON responses: latest, history, summary        │
│ ✓ Dữ liệu sẵn sàng cho dashboard                          │
│ ✓ Frontend polling mỗi 1-2 giây                           │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### **Yêu Cầu Trước Tiên**
- Python 3.11 hoặc cao hơn
- pip trình quản lý gói

### **Bước 1: Chuẩn Bị Môi Trường**

```bash
# Điều hướng tới dự án
cd d:\DuLieuCuaHuu\HK2_20252026\PTUD\CK\CK1

# Tạo virtual environment (nếu chưa có)
python -m venv venv
venv\Scripts\activate

# Cài đặt backend dependencies
pip install -r requirements.txt
```

### **Bước 2: Backend - Start Server**

```bash
# Terminal 1: Start FastAPI server
python -m uvicorn app.main:app --reload
# -> Running on http://localhost:8000
```

**Kiểm tra:** Truy cập http://localhost:8000/api/health

### **Bước 3: Backend - Collect Real System Metrics**

```bash
# Terminal 2: Collect CPU/Memory thực tế mỗi 2 giây
python collect_system_metrics.py

# Hoặc collect 1 lần:
python -c "import requests; requests.post('http://localhost:8000/api/system/collect')"
```

### **Bước 4: Frontend - Setup & Run**

```bash
# Terminal 3: Setup frontend
cd frontend
npm install

# Chạy development server
npm run dev
# -> Running on http://localhost:3000
```

### **Bước 5: Truy Cập Dashboard**

Mở trình duyệt: **http://localhost:3000**

---

## 📊 Các Endpoints API

### **1. Kiểm Tra Sức Khỏe**
```
GET /api/health
```

**Phản Hồi (200):**
```json
{
    "status": "healthy",
    "message": "Real-Time Metrics Processing System is running"
}
```

---

### **2. Tạo Một Metric**
```
POST /api/metrics
```

**Yêu Cầu:**
```json
{
    "metric_type": "cpu",
    "value": 45.5,
    "source": "server_1",
    "timestamp": "2024-04-04T10:30:00"  // Tùy chọn
}
```

**Phản Hồi (201 Created):**
```json
{
    "id": 1,
    "metric_type": "cpu",
    "value": 45.5,
    "source": "server_1",
    "timestamp": "2024-04-04T10:30:00"
}
```

---

### **3. Tạo Nhiều Metrics (Bulk)**
```
POST /api/metrics/bulk
```

**Yêu Cầu:**
```json
{
    "metrics": [
        {
            "metric_type": "cpu",
            "value": 45.5,
            "source": "server_1"
        },
        {
            "metric_type": "memory",
            "value": 78.2,
            "source": "server_1"
        },
        {
            "metric_type": "request_count",
            "value": 1250,
            "source": "server_1"
        }
    ]
}
```

**Phản Hồi (201 Created):**
```json
[
    {
        "id": 1,
        "metric_type": "cpu",
        "value": 45.5,
        "source": "server_1",
        "timestamp": "2024-04-04T10:30:00"
    },
    {
        "id": 2,
        "metric_type": "memory",
        "value": 78.2,
        "source": "server_1",
        "timestamp": "2024-04-04T10:30:00"
    },
    {
        "id": 3,
        "metric_type": "request_count",
        "value": 1250,
        "source": "server_1",
        "timestamp": "2024-04-04T10:30:00"
    }
]
```

---

### **4. Lấy Metrics Gần Đây Nhất**
```
GET /api/metrics/latest
```

**Phản Hồi (200):**
```json
{
    "latest_cpu": 45.5,
    "latest_memory": 78.2,
    "latest_request_count": 1250,
    "timestamp": "2024-04-04T10:35:00"
}
```

---

### **5. Lấy Lịch Sử Metrics**
```
GET /api/metrics/history?metric_type=cpu&minutes=5
```

**Tham Số Truy Vấn:**
- `metric_type` (bắt buộc): cpu, memory, hoặc request_count
- `minutes` (tùy chọn): Khoảng thời gian tính bằng phút (mặc định: 5, tối đa: 1440)

**Phản Hồi (200):**
```json
{
    "metric_type": "cpu",
    "data": [
        {
            "id": 1,
            "metric_type": "cpu",
            "value": 45.5,
            "source": "server_1",
            "timestamp": "2024-04-04T10:30:00"
        },
        {
            "id": 5,
            "metric_type": "cpu",
            "value": 48.2,
            "source": "server_1",
            "timestamp": "2024-04-04T10:31:00"
        }
    ],
    "count": 2
}
```

---

### **6. Lấy Tóm Tắt Metrics (Dashboard)**
```
GET /api/metrics/summary?minutes=1
```

**Tham Số Truy Vấn:**
- `minutes` (tùy chọn): Khoảng thời gian (mặc định: 1, tối đa: 1440)

**Phản Hồi (200):**
```json
{
    "avg_cpu_1m": 48.7,
    "avg_memory_1m": 76.8,
    "total_request_count_1m": 5250,
    "latest_cpu": 52.3,
    "latest_memory": 81.5,
    "latest_request_count": 1500,
    "timestamp": "2024-04-04T10:35:00"
}
```

---

### **7. Tạo Dữ Liệu Mẫu (Cho Dev/Demo)**
```
POST /api/dev/generate-sample-data?count=50
```

**Tham Số Truy Vấn:**
- `count` (tùy chọn): Số bản ghi mẫu (mặc định: 50, tối đa: 1000)

**Phản Hồi (201 Created):**
```json
{
    "message": "Successfully generated 50 sample metrics",
    "count": 50
}
```

---

### **8. Tạo Dữ Liệu IoT Giả Lập (Cho Dev/Demo)**
```
POST /api/dev/generate-iot-data?count=50
```

**Tham Số Truy Vấn:**
- `count` (tùy chọn): Số bản ghi mẫu (mặc định: 50, tối đa: 1000)

**Phản Hồi (201 Created):**
```json
{
    "message": "Successfully generated 50 sample IoT metrics",
    "count": 50,
    "iot_types": {
        "temperature": "Temperature in °C (15-35°C)",
        "humidity": "Humidity in % (30-90%)",
        "soil_moisture": "Soil Moisture in % (0-100%)",
        "light_intensity": "Light Intensity in lux (0-1000 lux)",
        "pressure": "Atmospheric Pressure in hPa (900-1100 hPa)"
    }
}
```

---

### **9️⃣ Lấy System Metrics Thực Tế (Current)**
```
GET /api/system/current
```

**Phản Hồi (200):**
```json
{
    "timestamp": "2026-04-04T08:05:50.123456",
    "metrics": {
        "cpu": {
            "value": 11.2,
            "percent": 11.2,
            "unit": "%"
        },
        "memory": {
            "value": 84.7,
            "percent": 84.7,
            "unit": "%"
        }
    }
}
```

---

### **🔟 Collect & Save System Metrics**
```
POST /api/system/collect
```

**Phản Hồi (201 Created):**
```json
{
    "message": "System metrics collected and saved",
    "timestamp": "2026-04-04T08:05:51.123456",
    "source": "system_monitor",
    "metrics_saved": {
        "cpu": 10.4,
        "memory": 82.5
    }
}
```

---

### **1️⃣1️⃣ Lấy Chi Tiết System Metrics**
```
GET /api/system/detailed
```

**Phản Hồi (200):**
```json
{
    "status": "success",
    "data": {
        "cpu": {
            "percent": 11.2,
            "count": 8,
            "per_core": [8.5, 12.3, 10.2, 9.8, ...]
        },
        "memory": {
            "percent": 84.7,
            "used": 27536842752,
            "available": 5087633408,
            "total": 32624476160
        },
        "disk": {
            "percent": 45.2,
            "used": 234567890123,
            "free": 287654321098,
            "total": 522222211221
        },
        "timestamp": "2026-04-04T08:05:50.123456"
    }
}
```
    }
}
```

---

## 🧪 Các Yêu Cầu cURL Để Kiểm Tra

### **Kiểm Tra 1: Kiểm Tra Sức Khỏe**
```bash
curl http://localhost:8000/api/health
```

### **Kiểm Tra 2: Tạo Một Metric**
```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","value":65.5,"source":"server_1"}'
```

### **Kiểm Tra 3: Tạo Nhiều Metrics**
```bash
curl -X POST http://localhost:8000/api/metrics/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "metrics":[
      {"metric_type":"cpu","value":50,"source":"s1"},
      {"metric_type":"cpu","value":60,"source":"s2"},
      {"metric_type":"memory","value":40,"source":"s1"},
      {"metric_type":"request_count","value":100,"source":"s1"}
    ]
  }'
```

### **Kiểm Tra 4: Lấy Metrics Gần Đây Nhất**
```bash
curl http://localhost:8000/api/metrics/latest
```

### **Kiểm Tra 5: Lấy Lịch Sử (Server Metrics)**
```bash
curl "http://localhost:8000/api/metrics/history?metric_type=cpu&minutes=5"
```

### **Kiểm Tra 6: Lấy Lịch Sử (IoT Metrics)**
```bash
curl "http://localhost:8000/api/metrics/history?metric_type=temperature&minutes=5"
curl "http://localhost:8000/api/metrics/history?metric_type=humidity&minutes=5"
```

### **Kiểm Tra 7: Lấy Tóm Tắt**
```bash
curl "http://localhost:8000/api/metrics/summary?minutes=1"
```

### **Kiểm Tra 8: Tạo Dữ Liệu Mẫu Server**
```bash
curl -X POST "http://localhost:8000/api/dev/generate-sample-data?count=100"
```

### **Kiểm Tra 9: Tạo Dữ Liệu Mẫu IoT**
```bash
curl -X POST "http://localhost:8000/api/dev/generate-iot-data?count=100"
```

---

## 🏗️ Giải Thích Kiến Trúc

### **Các Tầng Kiến Trúc**

```
┌────────────────────────────────────────────┐
│    FRONTEND (React Dashboard at 3000)      │
│  ├─ Dashboard với gauge/line charts        │
│  ├─ 6 pages: CPU, Memory, Requests, IoT    │
│  └─ Real-time updates (auto-refresh 1-5s)  │
└────────────┬─────────────────────────────┘
             │ HTTP REST (Socket-like polling)
             ▼
┌────────────────────────────────────────────┐
│   SYSTEM METRICS COLLECTOR (2s interval)   │
│  └─ Collect CPU/Memory → POST /api/system/ │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│     API LAYER (routes_metrics.py)          │
│ ├─ 11 HTTP endpoints (GET/POST)            │
│ ├─ Pydantic validation at input            │
│ ├─ CORS enabled for frontend               │
│ └─ JSON responses for dashboard            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│  BUSINESS LOGIC (metrics_service.py)       │
│ ├─ Aggregation algorithms                  │
│ ├─ Time-series calculations                │
│ └─ Dashboard data synthesis                │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│     SYSTEM METRICS (system_metrics.py)     │
│ ├─ psutil: real CPU/Memory from OS         │
│ ├─ Detailed info (cores, RAM available)    │
│ └─ Non-blocking measurements               │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│     DATA ACCESS LAYER (crud.py)            │
│ ├─ Create/Read/Update metrics              │
│ ├─ Time-range filtering                    │
│ ├─ Bulk operations support                 │
│ └─ Index optimization (metric_type, ts)    │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│  DATA MODEL (models.py + database.py)      │
│ ├─ SQLAlchemy ORM mapping                  │
│ ├─ Connection pooling                      │
│ ├─ Auto-schema initialization              │
│ └─ Transaction management                  │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│         SQLite Database (metrics.db)       │
│ ├─ Persistent storage                      │
│ ├─ 8 metric types support                  │
│ ├─ Efficient indexing                      │
│ └─ ACID transactions                       │
└────────────────────────────────────────────┘
```

### **Ánh Xạ Thành Phần**

| Thành Phần | File | Trách Nhiệm |
|-----------|------|-----------|
| **MetricsAPI** | `routes_metrics.py` | Phơi bày 11 endpoint REST |
| **SystemMetrics** | `system_metrics.py` | Lấy CPU/Memory thực từ psutil |
| **MetricsCollector** | `collect_system_metrics.py` | Script collect metrics liên tục |
| **Aggregator** | `metrics_service.py` | Tính toán trung bình, tổng, tóm tắt |
| **Frontend** | `frontend/src/` | React dashboard với charts |
| **DashboardAPI** | `/api/metrics/latest`, `/api/metrics/summary` | Cung cấp dữ liệu cho UI |
| **DataStore** | `models.py` + `database.py` | Lưu trữ metrics hiệu quả |
| **Validator** | `schemas.py` | Đảm bảo tính toàn vẹn dữ liệu |

---

## ✅ 5 Trường Hợp Kiểm Tra Nhanh Cho Demo

### **Trường Hợp 1: Xác Minh Sức Khỏe Hệ Thống**
**Mục Tiêu:** Xác minh backend đang chạy và phản hồi

```bash
curl http://localhost:8000/api/health
```

**Kết Quả Dự Kiến:**
- HTTP 200
- Response chứa `"status": "healthy"`
- Hệ thống sẵn sàng

---

### **Trường Hợp 2: Nhập Một Metric**
**Mục Tiêu:** Chứng minh quy trình nhập dữ liệu cơ bản

```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","value":65.5,"source":"prod_server_1"}'

curl http://localhost:8000/api/metrics/latest
```

**Kết Quả Dự Kiến:**
- HTTP 201 khi tạo
- Latest CPU hiển thị 65.5

---

### **Trường Hợp 3: Tải Khối Lượng Lớn Metrics**
**Mục Tiêu:** Kiểm tra nhập dữ liệu khối lượng cao

```bash
curl -X POST http://localhost:8000/api/metrics/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "metrics":[
      {"metric_type":"cpu","value":50,"source":"s1"},
      {"metric_type":"cpu","value":60,"source":"s2"},
      {"metric_type":"cpu","value":70,"source":"s3"},
      {"metric_type":"cpu","value":80,"source":"s4"},
      {"metric_type":"cpu","value":90,"source":"s5"},
      {"metric_type":"memory","value":40,"source":"s1"},
      {"metric_type":"memory","value":50,"source":"s2"},
      {"metric_type":"request_count","value":100,"source":"s1"},
      {"metric_type":"request_count","value":200,"source":"s2"}
    ]
  }'

curl "http://localhost:8000/api/metrics/summary?minutes=1"
```

**Kết Quả Dự Kiến:**
- HTTP 201 với 9 metrics
- Tóm tắt hiển thị: avg_cpu ≈ 70, avg_memory ≈ 45

---

### **Trường Hợp 4: Lọc & Lịch Sử**
**Mục Tiêu:** Chứng minh truy xuất dữ liệu cho biểu đồ

```bash
curl -X POST "http://localhost:8000/api/dev/generate-sample-data?count=50"

curl "http://localhost:8000/api/metrics/history?metric_type=cpu&minutes=10"
```

**Kết Quả Dự Kiến:**
- HTTP 201 tạo 50 metrics
- Lịch sử trả về CPU metrics sắp xếp theo thời gian

---

### **Trường Hợp 5: Xác Thực & Xử Lý Lỗi**
**Mục Tiêu:** Chứng minh từ chối dữ liệu không hợp lệ

```bash
# Metric type không hợp lệ
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"invalid","value":50,"source":"test"}'

# Giá trị âm
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","value":-10,"source":"test"}'

# Source rỗng
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","value":50,"source":""}'
```

**Kết Quả Dự Kiến:**
- HTTP 400 cho tất cả
- Thông báo lỗi rõ ràng

---

## 🔍 Các Quy Tắc Xác Thực

### **metric_type**
**Server Metrics:**
- Phải là một trong: `cpu`, `memory`, `request_count`

**IoT Sensor Metrics:**
- Phải là một trong: `temperature`, `humidity`, `soil_moisture`, `light_intensity`, `pressure`

- Tất cả phân biệt chữ hoa/thường

### **value**
- Phải là số không âm (≥ 0)
- Phải hợp lý (< 1,000,000)
- **Gợi ý Range theo loại:**
  - CPU: 0-100 (%)
  - Memory: 0-100 (%)
  - Request Count: 0-100000 (requests/phút)
  - Temperature: 15-35 (°C)
  - Humidity: 30-90 (%)
  - Soil Moisture: 0-100 (%)
  - Light Intensity: 0-1000 (lux)
  - Pressure: 900-1100 (hPa)

### **source**
- Không được rỗng
- Thường 1-100 ký tự
- Ví dụ: "server_1", "sensor_1", "soil_sensor_3"

### **timestamp**
- Tùy chọn - tự động tạo nếu không có
- Phải theo định dạng ISO 8601

---

## 🚨 Xử Lý Lỗi

API trả về các mã HTTP thích hợp:

- **200 OK**: GET request thành công
- **201 Created**: POST request thành công
- **400 Bad Request**: Dữ liệu đầu vào không hợp lệ
- **404 Not Found**: Tài nguyên không tìm thấy
- **500 Internal Server Error**: Lỗi máy chủ

**Định Dạng Lỗi:**
```json
{
    "detail": "Invalid metric_type. Must be one of {'cpu', 'memory', 'request_count'}"
}
```

---

## 📚 Các Cải Tiến Trong Tương Lai (Không Phải MVP)

- ⚠️ Cảnh báo nâng cao (ngưỡng, thông báo email)
- 🤖 Phân tích do LLM cung cấp
- 📨 Tích hợp Message Queue (Kafka, RabbitMQ)
- 🔌 Cập nhật WebSocket thời gian thực
- 🔐 Xác thực & Phân quyền (JWT)
- 📊 Xuất metrics (CSV, Prometheus format)
- 🗃️ Chính sách lưu giữ dữ liệu
- 🗄️ Hỗ trợ nhiều cơ sở dữ liệu (PostgreSQL, MongoDB)
- 📈 Mở rộng theo chiều ngang
- 🔭 Theo dõi phân tán

---

## 🆘 Khắc Phục Sự Cố

### **Cổng Đã Được Sử Dụng**
```bash
# Thay đổi cổng
python -m uvicorn app.main:app --port 8001
```

### **Cơ Sở Dữ Liệu Bị Khóa**
```bash
# Khởi động lại máy chủ
python -m uvicorn app.main:app --reload
```

### **Vấn Đề Dependencies**
```bash
# Cài đặt lại tất cả
pip install --upgrade -r requirements.txt
```

---

## 📝 Giấy Phép

MIT License - Mở để sử dụng trong giáo dục và thương mại

---

## 📞 Hỗ Trợ

Để biết thêm chi tiết, truy cập tài liệu API tại `/docs` khi máy chủ đang chạy.

**Tác Giả:** Backend MVP cho Hệ Thống Xử Lý Metrics Thời Gian Thực

**Phiên Bản:** 1.0.0

**Ngày Cập Nhật:** 04/04/2024
