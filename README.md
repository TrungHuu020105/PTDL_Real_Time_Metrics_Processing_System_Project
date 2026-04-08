# Real-Time Metrics Processing System 📊

> Hệ Thống Xử Lý Metrics Thời Gian Thực với Frontend Dashboard + Backend API

Một giải pháp hoàn chỉnh theo dõi hiệu suất hệ thống thời gian thực với **frontend React** và **backend FastAPI**, hỗ trợ **CPU/Memory thực tế** + **dữ liệu cảm biến IoT**.

---

## 👥 Nhóm

| Thứ Tự | Tên | MSSV |
|--------|-----|------|
| **Thành viên 1** | Huỳnh Nhật Hào | 23663871 |
| **Thành viên 2** | Lê Trung Hữu | 23666491 |
| **Thành viên 3** | Phan Gia Huy | 23674141 |
| **Thành viên 4** | Trần Quốc Huy | 23637731 |

---

## 🎯 Tổng Quan Dự Án

Hệ thống giám sát metrics thời gian thực gồm:

### **Backend** (FastAPI + SQLite)
- ✅ **8 REST API endpoints** - Nhập, truy xuất, tổng hợp metrics
- ✅ **CPU/Memory thực tế** - Sử dụng `psutil` để lấy số liệu từ máy
- ✅ **Server Metrics** - CPU, Memory, Request Count
- ✅ **IoT Sensors** - Temperature, Humidity, Soil Moisture, Light Intensity, Pressure
- ✅ **Bộ sưu tập liên tục** - Script tự động collect metrics mỗi 2 giây
- ✅ **Dashboard API** - Endpoints tối ưu cho frontend

### **Frontend** (React + Vite + Tailwind)
- ✅ **Dashboard chính** - Gauge charts + metric cards với real-time updates
- ✅ **6 trang chi tiết** - CPU, Memory, Requests, IoT Sensors, Alerts, Status
- ✅ **Biểu đồ động** - Line charts, bar charts, gauge indicators
- ✅ **Dark theme** - Neon cyan/purple/green colors, tối ưu cho chế độ tối
- ✅ **Auto-refresh** - Cập nhật 1-5 giây tùy theo trang
- ✅ **Sidebar navigation** - Menu dễ sử dụng

---

## 🛠️ Tech Stack

### **Backend**
- Python 3.11 + FastAPI + Uvicorn
- SQLAlchemy ORM + SQLite
- Pydantic validation
- psutil (system metrics)

### **Frontend**
- React 18 + Vite
- Tailwind CSS + Lucide Icons
- Recharts (data visualization)
- Axios (HTTP client)

---

## 📁 Cấu Trúc Dự Án

```
CK1/
├── app/                          # Backend FastAPI
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── database.py               # SQLite config
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic validation
│   ├── crud.py                   # Database operations
│   ├── system_metrics.py          # 🆕 Real system metrics collector
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes_metrics.py      # 8 REST endpoints
│   └── services/
│       ├── __init__.py
│       └── metrics_service.py     # Business logic
│
├── frontend/                     # 🆕 React + Vite Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx       # Navigation menu
│   │   │   ├── Dashboard.jsx     # Main dashboard
│   │   │   ├── GaugeChart.jsx    # Gauge indicators
│   │   │   ├── MetricCard.jsx    # Metric cards
│   │   │   ├── CPUMetrics.jsx    # CPU detail page
│   │   │   ├── MemoryMetrics.jsx # Memory detail page
│   │   │   ├── RequestMetrics.jsx # Requests detail page
│   │   │   ├── IoTMetrics.jsx    # IoT sensors page
│   │   │   └── Alerts.jsx        # Alerts page
│   │   ├── App.jsx               # Main app component
│   │   ├── api.js                # Axios client
│   │   ├── main.jsx              # React entry point
│   │   └── index.css             # Tailwind styles
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── metrics.db                     # SQLite database (auto-created)
├── requirements.txt               # Python dependencies
├── generate_iot_data.py           # IoT data generator script
├── collect_system_metrics.py      # 🆕 Continuous system metrics collector
├── README.md                      # This file
└── .gitignore                     # Git ignore rules
```

---

## ⚡ Quick Start (5 phút)

```bash
# Terminal 1: Backend
python -m uvicorn app.main:app --reload

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Terminal 2: Collect metrics
python collect_system_metrics.py

# Terminal 3: Frontend
cd frontend && npm install && npm run dev

# Terminal 4: Generate test data (optional)
python generate_iot_data.py --count 500 --spread-hours 24

# chạy liên tục vưới terminal4
python generate_iot_data.py --continuous --interval 2
```

**Khi hoàn tất:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 🚀 Hướng Dẫn Chạy Hệ Thống

### **Bộ Dữ Liệu Là Gì?**

Hệ thống lưu trữ **8 loại metrics** trong SQLite (`metrics.db`):

- **Server Metrics** (3 loại): CPU (%), Memory (%), Request Count
- **IoT Sensors** (5 loại): Temperature (°C), Humidity (%), Soil Moisture (%), Light Intensity (lux), Pressure (hPa)

Mỗi bản ghi chứa:
```json
{
    "id": 1,
    "metric_type": "cpu",           // Loại metric
    "value": 45.5,                  // Giá trị
    "source": "system_monitor",     // Nguồn dữ liệu
    "timestamp": "2026-04-04T08:05:50"  // Thời gian
}
```

---

### **Dữ Liệu Sinh Ra Từ 4 Nguồn Chính**

#### **1️⃣ Từ Hệ Thống Thực (🆕 Real System Metrics)**

Sử dụng `psutil` để lấy CPU/Memory **thực tế từ máy**:

```bash
# Collect và save tự động mỗi 2 giây
python collect_system_metrics.py

# Hoặc endpoint API lấy ngay
curl http://localhost:8000/api/system/current
```

**Kết Quả:**
```json
{
    "metrics": {
        "cpu": {"value": 11.2, "unit": "%"},
        "memory": {"value": 84.7, "unit": "%"}
    }
}
```

#### **2️⃣ Từ API Metrics (Frontend/Client)**

Ứng dụng khác gửi metrics qua HTTP POST:

```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","value":65.5,"source":"server_1"}'
```

#### **3️⃣ Từ Dữ Liệu Giả Lập (Testing)**

Endpoint dev để sinh fake data cho testing:
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "cpu",
    "value": 65.5,
    "source": "server_1"
  }'
```

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
