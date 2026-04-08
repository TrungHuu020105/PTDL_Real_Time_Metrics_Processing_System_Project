"""
Pydantic schemas cho WebSocket metrics (Pydantic v2)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MetricsData(BaseModel):
    """
    Schema cho dữ liệu metrics nhận được từ client.
    - cpu: CPU usage in percentage (0-100)
    - ram: RAM usage in percentage (0-100)
    - timestamp: Timestamp khi dữ liệu được lấy
    """
    cpu: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    ram: float = Field(..., ge=0, le=100, description="RAM usage percentage")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cpu": 45.5,
                "ram": 72.3,
                "timestamp": "2024-04-06T10:30:00.123456"
            }
        }
    }


class ClientStatus(BaseModel):
    """
    Schema cho thông tin status của một client.
    """
    client_id: str
    status: str
    connected_at: Optional[str] = None
    last_update: Optional[str] = None
    metrics: Optional[MetricsData] = None


class StatusResponse(BaseModel):
    """
    Schema cho response của endpoint /status.
    """
    total_clients: int
    timestamp: str
    clients: List[ClientStatus]
