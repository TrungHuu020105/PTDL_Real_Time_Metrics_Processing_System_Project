"""IoT Device management routes - User-owned devices"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IoTDevice, User
from app.api.routes_auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/iot-devices", tags=["iot-devices"])


# ============== SCHEMAS ==============

class CreateIoTDeviceRequest(BaseModel):
    """Request schema for creating IoT device"""
    name: str
    device_type: str
    source: str
    location: str = None


# ============== IoT DEVICE MANAGEMENT ==============

@router.post("")
async def create_iot_device(
    device_data: CreateIoTDeviceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new IoT device - User owned"""
    # Check if source already exists
    existing = db.query(IoTDevice).filter(IoTDevice.source == device_data.source).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source '{device_data.source}' already exists"
        )
    
    device = IoTDevice(
        user_id=user.id,
        name=device_data.name,
        device_type=device_data.device_type,
        source=device_data.source,
        location=device_data.location,
        is_active=True
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return {
        "id": device.id,
        "name": device.name,
        "device_type": device.device_type,
        "source": device.source,
        "location": device.location,
        "is_active": device.is_active,
        "created_at": device.created_at
    }


@router.get("")
async def get_my_iot_devices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all IoT devices owned by current user"""
    devices = db.query(IoTDevice).filter(IoTDevice.user_id == user.id).all()
    
    return {
        "devices": [
            {
                "id": d.id,
                "name": d.name,
                "device_type": d.device_type,
                "source": d.source,
                "location": d.location,
                "is_active": d.is_active,
                "created_at": d.created_at
            }
            for d in devices
        ],
        "count": len(devices)
    }


@router.put("/{device_id}")
async def update_iot_device(
    device_id: int,
    name: str = None,
    location: str = None,
    is_active: bool = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update IoT device - Only owner can update"""
    device = db.query(IoTDevice).filter(
        IoTDevice.id == device_id,
        IoTDevice.user_id == user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if name:
        device.name = name
    if location is not None:
        device.location = location
    if is_active is not None:
        device.is_active = is_active
    
    db.commit()
    db.refresh(device)
    
    return {
        "id": device.id,
        "name": device.name,
        "device_type": device.device_type,
        "source": device.source,
        "location": device.location,
        "is_active": device.is_active,
        "created_at": device.created_at
    }


@router.delete("/{device_id}")
async def delete_iot_device(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete IoT device - Only owner can delete"""
    device = db.query(IoTDevice).filter(
        IoTDevice.id == device_id,
        IoTDevice.user_id == user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()
    
    return {"message": "Device deleted successfully"}
