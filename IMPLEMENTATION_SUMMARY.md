# 📋 WebSocket Implementation Summary

## 📁 Files Tạo Mới / Sửa Đổi

### **Server Files (Backend)**

| File | Mô Tả |
|------|-------|
| `app/websocket_manager.py` | ✨ NEW - ConnectionManager để quản lý clients |
| `app/schemas_ws.py` | ✨ NEW - Pydantic v2 schemas (MetricsData, ClientStatus, StatusResponse) |
| `app/api/routes_websocket.py` | ✨ NEW - WebSocket endpoints & API routes |
| `app/main.py` | 🔄 UPDATED - Include websocket routes |
| `requirements.txt` | 🔄 UPDATED - Thêm websockets==12.0 |

### **Client Files**

| File | Mô Tả |
|------|-------|
| `client_agent.py` | ✨ NEW - Client script với async WebSocket & psutil |

### **Documentation**

| File | Mô Tả |
|------|-------|
| `WEBSOCKET_GUIDE.md` | ✨ NEW - Hướng dẫn chi tiết |
| `QUICK_START.md` | ✨ NEW - Hướng dẫn nhanh (5 phút) |
| `test_websocket.py` | ✨ NEW - Test file |

---

## 🎯 Features Implemented

### **Server (app/websocket_manager.py)**
- ✅ ConnectionManager: Quản lý conns, metrics, status
- ✅ Async/await pattern
- ✅ Error handling
- ✅ Broadcast capability
- ✅ Detailed logging

### **Endpoints (app/api/routes_websocket.py)**
- ✅ `WebSocket /ws/{client_id}`: Nhận metrics, validate, lưu
- ✅ `GET /api/status`: Tất cả clients + metrics
- ✅ `GET /api/status/{client_id}`: Info một client
- ✅ `GET /api/health`: Health check

### **Schemas (app/schemas_ws.py - Pydantic v2)**
- ✅ MetricsData: cpu, ram, timestamp validation
- ✅ ClientStatus: client info schema
- ✅ StatusResponse: API response schema
- ✅ Field validation (ge=0, le=100)
- ✅ Model config examples

### **Client (client_agent.py)**
- ✅ MetricsCollector: psutil CPU/RAM
- ✅ WebSocketClient: Async connection, send metrics
- ✅ Retry logic: 5 attempts, 2 second delay
- ✅ Command-line arguments: --client-id, --server, --interval
- ✅ Error handling: ConnectionClosed, JSONDecodeError, etc
- ✅ Detailed logging

---

## 🚀 Chạy Hệ Thống

### **Terminal 1: Server**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Terminal 2, 3, 4...: Clients**
```bash
python client_agent.py --client-id "client_1"
python client_agent.py --client-id "client_2"
python client_agent.py --client-id "client_3"
```

### **Terminal 5: Monitor**
```bash
# Xem status
curl http://127.0.0.1:8000/api/status

# Xem health
curl http://127.0.0.1:8000/api/health

# Xem một client
curl http://127.0.0.1:8000/api/status/client_1
```

---

## 📊 Data Flow

```
Client Agent (client_agent.py)
    ↓ psutil.cpu_percent()
    ↓ psutil.virtual_memory()
    ↓ Create JSON: {"cpu": 45.5, "ram": 72.3, "timestamp": "..."}
    ↓ Send via WebSocket
    ↓
Server (app/api/routes_websocket.py)
    ↓ Receive JSON
    ↓ Validate with Pydantic MetricsData
    ↓ Call manager.save_metrics()
    ↓
ConnectionManager (app/websocket_manager.py)
    ↓ Update active_connections[client_id]
    ↓ Update client_metrics[client_id]
    ↓ Print log
    ↓
API Endpoint GET /status
    ↓ manager.get_all_status()
    ↓ Return JSON with all clients + latest metrics
    ↓
Client makes curl request to get status
```

---

## 🔧 Function Reference

### **ConnectionManager Methods**

```python
# Connect a new client
await manager.connect(client_id, websocket)

# Disconnect client
manager.disconnect(client_id)

# Save metrics from client
manager.save_metrics(client_id, data)

# Get all clients status
manager.get_all_status()

# Get single client info
manager.get_client_info(client_id)

# Broadcast to all clients
await manager.broadcast(message)
```

### **API Endpoints**

```
WebSocket:
  ws://SERVER_IP:8000/ws/{client_id}

HTTP GET:
  /api/status                    # All clients
  /api/status/{client_id}        # Single client
  /api/health                    # Health check
```

### **Client Arguments**

```bash
--client-id text     # Client identifier (default: hostname)
--server url         # WebSocket server URL (default: ws://192.168.137.1:8000)
--interval int       # Seconds between sends (default: 1)
```

---

## 🔍 Validation Rules (Pydantic v2)

```python
cpu: float
  - ge=0 (≥ 0)
  - le=100 (≤ 100)

ram: float
  - ge=0 (≥ 0)
  - le=100 (≤ 100)

timestamp: str
  - Format: ISO 8601
  - Auto-generate if not provided
```

---

## 📝 Logs Output

### **Server Logs**
```
✅ Client {client_id} đã kết nối. Tổng clients: N
📊 Nhận dữ liệu từ Client {client_id}: CPU=X%, RAM=Y%
❌ Client {client_id} đã thoát. Tổng clients còn lại: N
```

### **Client Logs**
```
🔗 Đang kết nối tới server: ws://...
✅ Client {client_id} đã kết nối thành công!
📤 [{client_id}] Gửi: CPU=X% | RAM=Y%
📥 [{client_id}] Server response: {...}
⚠️ Lỗi kết nối: ...
```

---

## ⚠️ Error Handling

### **Server Side**
- JSON decode errors → Send error response
- Pydantic validation errors → Send error response
- Connection closed → Disconnect client

### **Client Side**
- Connection refused → Retry 5 times (2s delay)
- WebSocket closed → Stop and report
- JSON send error → Catch and continue

---

## 📚 Documentation Files

- **WEBSOCKET_GUIDE.md** - Chi tiết đầy đủ (8 sections)
- **QUICK_START.md** - Ngắn gọn (4 steps)
- **This file** - Tóm tắt features & functions

---

## ✅ Checklist

- ✅ Server quản lý multiple clients
- ✅ Client collect real system metrics
- ✅ WebSocket bidirectional communication
- ✅ Pydantic v2 validation
- ✅ Async/await pattern
- ✅ Error handling & retry logic
- ✅ Detailed logging
- ✅ Command-line arguments
- ✅ API endpoints
- ✅ Health checks
- ✅ Documentation

---

## 🎓 Learning Points

1. **FastAPI WebSockets**: Integration with async
2. **Pydantic v2**: BaseModel, Field, validation
3. **psutil**: CPU/RAM collection
4. **asyncio**: async/await, tasks, timeouts
5. **websockets**: Client/server async communication
6. **Connection Management**: Lifecycle, tracking, broadcasts

---

**Version:** 1.0.0  
**Date:** 2024-04-06  
**Status:** ✅ Complete
