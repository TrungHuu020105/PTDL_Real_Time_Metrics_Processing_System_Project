"""
WebSocket routes cho Real-Time Metrics Monitoring
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.websocket_manager import ConnectionManager
from app.schemas_ws import MetricsData, StatusResponse
import json
from datetime import datetime

# Khởi tạo router
router = APIRouter(tags=["WebSocket Metrics"])

# Khởi tạo ConnectionManager (global)
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint để client kết nối và gửi metrics.
    
    Endpoint: ws://SERVER_IP:8000/ws/{client_id}
    
    Client gửi JSON format:
    {
        "cpu": 45.5,
        "ram": 72.3,
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
                
                # Validate với Pydantic schema
                metrics = MetricsData(**metrics_dict)
                
                # Lưu metrics
                manager.save_metrics(client_id, metrics.model_dump())
                
                # Gửi confirmation lại cho client (optional)
                await websocket.send_text(json.dumps({
                    "status": "ok",
                    "message": f"Metrics received from {client_id}",
                    "server_time": datetime.now().isoformat()
                }))
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error từ {client_id}: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }))
                
            except ValueError as e:
                print(f"⚠️ Validation error từ {client_id}: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": f"Validation error: {str(e)}"
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
