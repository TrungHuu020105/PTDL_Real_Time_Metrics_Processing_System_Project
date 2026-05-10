"""IoT Device management routes - User-owned devices"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from iot_backend.database import get_db
from iot_backend.models import IoTDevice, User, Device, UserDevicePermission
from iot_backend.api.routes_auth import get_current_user
from iot_backend import crud
from iot_backend.services.weather_service import geocode_location
import re

router = APIRouter(prefix="/api/iot-devices", tags=["iot-devices"])


def _normalize_environment_type(value: Optional[str]) -> str:
    env = (value or "indoor").strip().lower()
    return "outdoor" if env == "outdoor" else "indoor"


def _normalize_source(value: str) -> str:
    source = (value or "").strip().lower()
    match = re.fullmatch(r"sensor[-_]?0*(\d+)", source)
    if match:
        return f"sensor_{int(match.group(1))}"
    return source


# ============== SCHEMAS ==============

class CreateIoTDeviceRequest(BaseModel):
    """Request schema for creating IoT device"""
    name: str
    device_type: str
    source: str
    location: str = None
    environment_type: str = "indoor"  # indoor | outdoor
    location_query: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    task_description: Optional[str] = None
    priority_level: Optional[str] = None
    action_hint: Optional[str] = None


class UpdateAlertThresholdsRequest(BaseModel):
    """Request schema for updating alert thresholds"""
    alert_enabled: bool = False
    lower_threshold: Optional[float] = None  # Lower threshold (values below trigger alert)
    upper_threshold: Optional[float] = None  # Upper threshold (values above trigger alert)


class UpdateIoTDeviceRequest(BaseModel):
    """Request schema for updating user-owned IoT device."""
    name: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    environment_type: Optional[str] = None
    location_query: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    task_description: Optional[str] = None
    priority_level: Optional[str] = None
    action_hint: Optional[str] = None


class GeocodeRequest(BaseModel):
    location_query: str


# ============== IoT DEVICE MANAGEMENT ==============

@router.post("")
async def create_iot_device(
    device_data: CreateIoTDeviceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new IoT device - User owned. Also registers in Device table for metric generation."""
    try:
        normalized_source = _normalize_source(device_data.source)
        if not normalized_source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sensor source is required",
            )

        # Check if source already exists in IoTDevice (user-owned table)
        existing_iot = db.query(IoTDevice).filter(IoTDevice.source == normalized_source).first()
        
        if existing_iot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a device with source '{normalized_source}'. Each sensor can only be used once per user."
            )
        
        environment_type = _normalize_environment_type(device_data.environment_type)
        location_query = (device_data.location_query or "").strip() or None
        latitude = device_data.latitude
        longitude = device_data.longitude
        timezone_name = None

        if environment_type == "outdoor" and (latitude is None or longitude is None) and location_query:
            geo = geocode_location(location_query)
            if geo:
                latitude = geo.latitude
                longitude = geo.longitude
                timezone_name = geo.timezone

        # Step 1: Create IoTDevice (user-owned view)
        print(f"[DEBUG] Creating IoTDevice: {device_data.name} by user {user.id}")
        iot_device = IoTDevice(
            user_id=user.id,
            name=device_data.name,
            device_type=device_data.device_type,
            source=normalized_source,
            location=device_data.location,
            environment_type=environment_type,
            location_query=location_query,
            latitude=latitude,
            longitude=longitude,
            timezone_name=timezone_name,
            task_description=(device_data.task_description or "").strip() or None,
            priority_level=(device_data.priority_level or "").strip().lower() or None,
            action_hint=(device_data.action_hint or "").strip() or None,
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
        print(f"[DEBUG] Checking Device for metrics: {normalized_source}")
        existing_device = db.query(Device).filter(Device.source == normalized_source).first()
        
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
            print(f"[DEBUG] Creating Device for metrics: {normalized_source}")
            device = Device(
                name=device_data.name,
                device_type=device_data.device_type,
                source=normalized_source,
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
            "environment_type": iot_device.environment_type,
            "location_query": iot_device.location_query,
            "latitude": iot_device.latitude,
            "longitude": iot_device.longitude,
            "timezone_name": iot_device.timezone_name,
            "task_description": iot_device.task_description,
            "priority_level": iot_device.priority_level,
            "action_hint": iot_device.action_hint,
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
                "environment_type": d.environment_type,
                "location_query": d.location_query,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "timezone_name": d.timezone_name,
                "task_description": d.task_description,
                "priority_level": d.priority_level,
                "action_hint": d.action_hint,
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
    update_data: UpdateIoTDeviceRequest,
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
    
    if update_data.name is not None and update_data.name.strip():
        device.name = update_data.name.strip()
    if update_data.device_type is not None and update_data.device_type.strip():
        device.device_type = update_data.device_type.strip()
    if update_data.location is not None:
        device.location = update_data.location
    if update_data.is_active is not None:
        device.is_active = update_data.is_active
    if update_data.environment_type is not None:
        device.environment_type = _normalize_environment_type(update_data.environment_type)
    if update_data.location_query is not None:
        device.location_query = update_data.location_query.strip() or None
    if update_data.latitude is not None:
        device.latitude = update_data.latitude
    if update_data.longitude is not None:
        device.longitude = update_data.longitude
    if update_data.task_description is not None:
        device.task_description = update_data.task_description.strip() or None
    if update_data.priority_level is not None:
        device.priority_level = update_data.priority_level.strip().lower() or None
    if update_data.action_hint is not None:
        device.action_hint = update_data.action_hint.strip() or None

    if (
        device.environment_type == "outdoor"
        and (device.latitude is None or device.longitude is None)
        and device.location_query
    ):
        geo = geocode_location(device.location_query)
        if geo:
            device.latitude = geo.latitude
            device.longitude = geo.longitude
            device.timezone_name = geo.timezone

    # Keep metrics-generation Device row in sync where possible.
    admin_device = db.query(Device).filter(Device.source == device.source).first()
    if admin_device:
        admin_device.name = device.name
        admin_device.device_type = device.device_type
        admin_device.location = device.location
        if update_data.is_active is not None:
            admin_device.is_active = update_data.is_active

    db.commit()
    db.refresh(device)
    
    return {
        "id": device.id,
        "name": device.name,
        "device_type": device.device_type,
        "source": device.source,
        "location": device.location,
        "environment_type": device.environment_type,
        "location_query": device.location_query,
        "latitude": device.latitude,
        "longitude": device.longitude,
        "timezone_name": device.timezone_name,
        "task_description": device.task_description,
        "priority_level": device.priority_level,
        "action_hint": device.action_hint,
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

@router.post("/geocode")
async def geocode_sensor_location(
    payload: GeocodeRequest,
    user: User = Depends(get_current_user),
):
    """Resolve a location string to lat/lon for outdoor sensors."""
    geo = geocode_location(payload.location_query)
    if not geo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return {
        "name": geo.name,
        "country": geo.country,
        "admin1": geo.admin1,
        "timezone": geo.timezone,
        "latitude": geo.latitude,
        "longitude": geo.longitude,
    }

