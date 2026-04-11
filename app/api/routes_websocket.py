"""
WebSocket routes cho Real-Time Metrics Monitoring
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.websocket_manager import ConnectionManager
from app.schemas_ws import MetricsData, IotMetricsData, StatusResponse
from app.schemas import MetricCreate
from app.database import SessionLocal
from app.crud import create_metrics_bulk
import json
from datetime import datetime

# Khởi tạo router
router = APIRouter(tags=["WebSocket Metrics"])

# Khởi tạo ConnectionManager (global)
manager = ConnectionManager()


def save_iot_metric_to_db(metric_type: str, source: str, value: float, save_flag: bool):
    """
    Save IoT metric to database - but only if save_flag is True
    
    Architecture:
    - Frontend receives 100% of realtime data (smooth display)
    - Database only saves "important" data (filtered by threshold)
    This separates realtime streaming from intelligent persistence
    """
    # Log to file for debugging
    with open("backend_filtering.log", "a") as f:
        f.write(f"{metric_type}={value} | saved={save_flag}\n")
    
    if not save_flag:
        return  # Skip DB save for non-important data
    
    try:
        db = SessionLocal()
        metric = MetricCreate(
            metric_type=metric_type,
            value=value,
            source=source,
            timestamp=None
        )
        create_metrics_bulk(db, [metric])
        db.close()
        print(f"💾 Saved {metric_type}={value} (source={source}) to DB")
    except Exception as e:
        print(f"❌ DB save error: {e}")
        if db:
            db.close()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint để client kết nối và gửi metrics.
    
    Endpoint: ws://SERVER_IP:8000/api/ws/{client_id}
    
    Hỗ trợ 2 loại metrics:
    
    1. System Metrics (CPU/RAM):
    {
        "cpu": 45.5,
        "ram": 72.3,
        "timestamp": "2024-04-06T10:30:00"
    }
    
    2. IoT Sensor Metrics:
    {
        "metric_type": "temperature",
        "value": 24.5,
        "source": "sensor_1",
        "unit": "°C",
        "timestamp": "2024-04-06T10:30:00"
    }
    """
    try:
        # Kết nối client
        print(f"🔗 [DEBUG] Client {client_id} đang cố kết nối...")
        await manager.connect(client_id, websocket)
        print(f"✅ [DEBUG] Client {client_id} đã accept WebSocket!")
        
        # Lặp nhận dữ liệu từ client
        while True:
            try:
                # Nhận dữ liệu JSON từ client
                data = await websocket.receive_text()
                
                # Parse JSON
                metrics_dict = json.loads(data)
                
                # Try IoT metrics first (has metric_type field)
                if "metric_type" in metrics_dict:
                    try:
                        metrics = IotMetricsData(**metrics_dict)
                        manager.save_metrics(client_id, metrics.model_dump())
                        # DEBUG: Print received saved flag
                        print(f"[DEBUG] Received: {metrics.metric_type} | saved={metrics.saved}")
                        # Save to database - but only if "saved" flag is True
                        save_iot_metric_to_db(
                            metrics.metric_type, 
                            metrics.source, 
                            metrics.value,
                            metrics.saved  # Check "saved" flag for DB filtering
                        )
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "status": "ok",
                            "message": f"IoT metric received: {metrics.metric_type}",
                            "server_time": datetime.now().isoformat()
                        }))
                    except ValueError as e:
                        print(f"⚠️ IoT Validation error từ {client_id}: {e}")
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": f"IoT Validation error: {str(e)}"
                        }))
                # Else try system metrics (CPU/RAM)
                else:
                    try:
                        metrics = MetricsData(**metrics_dict)
                        manager.save_metrics(client_id, metrics.model_dump())
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "status": "ok",
                            "message": f"System metrics received from {client_id}",
                            "server_time": datetime.now().isoformat()
                        }))
                    except ValueError as e:
                        print(f"⚠️ System Validation error từ {client_id}: {e}")
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": f"System Validation error: {str(e)}"
                        }))
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error từ {client_id}: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }))
                    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ Error với client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status():
    """
    GET endpoint để lấy trạng thái tất cả clients và metrics mới nhất.
    
    Response format:
    {
        "total_clients": 3,
        "timestamp": "2024-04-06T10:35:00",
        "clients": [
            {
                "client_id": "client_1",
                "status": "online",
                "connected_at": "2024-04-06T10:30:00",
                "last_update": "2024-04-06T10:35:00",
                "metrics": {
                    "cpu": 45.5,
                    "ram": 72.3,
                    "timestamp": "2024-04-06T10:35:00"
                }
            }
        ]
    }
    """
    return manager.get_all_status()


@router.get("/status/{client_id}", tags=["Status"])
async def get_client_status(client_id: str):
    """
    GET endpoint để lấy thông tin của một client cụ thể.
    
    Parameters:
    - client_id: ID của client
    """
    client_info = manager.get_client_info(client_id)
    
    if client_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client {client_id} không tìm thấy hoặc chưa kết nối"
        )
    
    return client_info


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "message": "WebSocket Metrics Server is running",
        "connected_clients": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }
