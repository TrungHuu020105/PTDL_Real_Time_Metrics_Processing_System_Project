"""IoT Device management routes - User-owned devices"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IoTDevice, User, Device, UserDevicePermission
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


class UpdateAlertThresholdsRequest(BaseModel):
    """Request schema for updating alert thresholds"""
    alert_enabled: bool = False
    lower_threshold: Optional[float] = None  # Lower threshold (values below trigger alert)
    upper_threshold: Optional[float] = None  # Upper threshold (values above trigger alert)


# ============== IoT DEVICE MANAGEMENT ==============

@router.post("")
async def create_iot_device(
    device_data: CreateIoTDeviceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new IoT device - User owned. Also registers in Device table for metric generation."""
    try:
        # Check if source already exists in IoTDevice (user-owned table)
        existing_iot = db.query(IoTDevice).filter(IoTDevice.source == device_data.source).first()
        
        if existing_iot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a device with source '{device_data.source}'. Each sensor can only be used once per user."
            )
        
        # Step 1: Create IoTDevice (user-owned view)
        print(f"[DEBUG] Creating IoTDevice: {device_data.name} by user {user.id}")
        iot_device = IoTDevice(
            user_id=user.id,
            name=device_data.name,
            device_type=device_data.device_type,
            source=device_data.source,
            location=device_data.location,
            is_active=True,
            alert_enabled=False,
            lower_threshold=None,
            upper_threshold=None
        )
        db.add(iot_device)
        db.commit()
        db.refresh(iot_device)
        print(f"[OK] IoTDevice created: {iot_device.id}")
        
        # Step 2: Check if Device record exists, if not create it
        print(f"[DEBUG] Checking Device for metrics: {device_data.source}")
        existing_device = db.query(Device).filter(Device.source == device_data.source).first()
        
        if existing_device:
            # Device already exists (from demo or other user)
            # Enable it if not already active
            if not existing_device.is_active:
                print(f"[DEBUG] Enabling existing Device: {existing_device.id}")
                existing_device.is_active = True
                db.commit()
                db.refresh(existing_device)
            print(f"[OK] Device already exists: {existing_device.id}, active={existing_device.is_active}")
            device = existing_device
        else:
            # Create new Device record with is_active=True for metric generation
            print(f"[DEBUG] Creating Device for metrics: {device_data.source}")
            device = Device(
                name=device_data.name,
                device_type=device_data.device_type,
                source=device_data.source,
                location=device_data.location,
                is_active=True,  # Enable metrics generation immediately
                created_by=user.id
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            print(f"[OK] Device created: {device.id} with is_active=True")
        
        # Step 3: Grant user permission to view this device
        print(f"[DEBUG] Creating UserDevicePermission")
        permission = UserDevicePermission(
            user_id=user.id,
            device_id=device.id,
            granted_by=user.id
        )
        db.add(permission)
        db.commit()
        print(f"[OK] Permission granted")
        
        return {
            "id": iot_device.id,
            "name": iot_device.name,
            "device_type": iot_device.device_type,
            "source": iot_device.source,
            "location": iot_device.location,
            "is_active": iot_device.is_active,
            "alert_enabled": iot_device.alert_enabled,
            "lower_threshold": iot_device.lower_threshold,
            "upper_threshold": iot_device.upper_threshold,
            "created_at": iot_device.created_at,
            "message": "✅ Device created successfully. Metric generation started immediately!"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create device: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device: {str(e)}"
        )


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
                "alert_enabled": d.alert_enabled,
                "lower_threshold": d.lower_threshold,
                "upper_threshold": d.upper_threshold,
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
        "alert_enabled": device.alert_enabled,
        "lower_threshold": device.lower_threshold,
        "upper_threshold": device.upper_threshold,
        "created_at": device.created_at
    }


@router.delete("/{device_id}")
async def delete_iot_device(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete IoT device - Only owner can delete. Also deletes corresponding Device record."""
    device = db.query(IoTDevice).filter(
        IoTDevice.id == device_id,
        IoTDevice.user_id == user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Disable corresponding Device record (for metric generation)
    # Don't delete - keep historical data
    print(f"[DEBUG] Disabling Device for metrics: {device.source}")
    admin_device = db.query(Device).filter(Device.source == device.source).first()
    if admin_device:
        admin_device.is_active = False
        db.commit()
        print(f"[OK] Device disabled: {admin_device.id}, metrics generation stopped")
    
    # Delete IoTDevice (user-owned view)
    db.delete(device)
    db.commit()
    
    return {"message": "Device deleted successfully. Metrics generation stopped. Historical data preserved."}


@router.put("/{device_id}/alert-thresholds")
async def update_alert_thresholds(
    device_id: int,
    alert_data: UpdateAlertThresholdsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update alert thresholds for a device - Only owner can update"""
    device = db.query(IoTDevice).filter(
        IoTDevice.id == device_id,
        IoTDevice.user_id == user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update alert settings
    device.alert_enabled = alert_data.alert_enabled
    device.lower_threshold = alert_data.lower_threshold
    device.upper_threshold = alert_data.upper_threshold
    
    db.commit()
    db.refresh(device)
    
    return {
        "id": device.id,
        "name": device.name,
        "device_type": device.device_type,
        "source": device.source,
        "alert_enabled": device.alert_enabled,
        "lower_threshold": device.lower_threshold,
        "upper_threshold": device.upper_threshold,
        "message": "✅ Alert thresholds updated successfully"
    }
