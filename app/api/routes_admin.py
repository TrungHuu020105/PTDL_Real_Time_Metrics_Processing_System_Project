"""Admin management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, IoTDevice
from app.schemas import DeviceCreate, DeviceUpdate, DeviceResponse, UserResponse
from app.api.routes_auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(user: User = Depends(get_current_user)) -> User:
    """Verify that current user is admin"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    return user


# ============== USER MANAGEMENT ==============

@router.get("/users/pending")
async def get_pending_users(admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Get users pending approval"""
    users = crud.get_pending_users(db)
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at
            }
            for u in users
        ],
        "count": len(users)
    }


@router.post("/users/{user_id}/approve")
async def approve_user(user_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin approves a pending user"""
    user = crud.approve_user(db, user_id, admin.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": f"User {user.username} approved successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_approved": user.is_approved,
            "approved_at": user.approved_at
        }
    }


@router.post("/users/{user_id}/reject")
async def reject_user(user_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin rejects a pending user"""
    success = crud.reject_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already approved"
        )
    
    return {"message": "User rejected and deleted"}


@router.get("/users")
async def get_all_users(admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Get all users"""
    users = crud.get_all_users(db)
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_approved": u.is_approved,
                "created_at": u.created_at
            }
            for u in users
        ],
        "count": len(users)
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin deletes a user"""
    # Prevent deleting self
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = crud.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


# ============== DEVICE MANAGEMENT ==============

@router.post("/devices", response_model=DeviceResponse, status_code=201)
async def create_device(device: DeviceCreate, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Create a new device"""
    # Check if source already exists
    existing = crud.get_device_by_source(db, device.source)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this source already exists"
        )
    
    db_device = crud.create_device(db, device, admin.id)
    return db_device


@router.get("/devices")
async def get_all_devices(admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Get all devices"""
    devices = crud.get_all_devices(db)
    return {
        "devices": devices,
        "count": len(devices)
    }


@router.delete("/devices/{device_id}")
async def delete_device(device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Delete a device"""
    success = crud.delete_device(db, device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": "Device deleted successfully"}


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, device_update: DeviceUpdate, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Update device information (name, device_type, location)"""
    # Get the device first to check if it exists
    db_device = crud.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update only provided fields
    if device_update.name is not None:
        db_device.name = device_update.name
    if device_update.device_type is not None:
        db_device.device_type = device_update.device_type
    if device_update.location is not None:
        db_device.location = device_update.location
    
    db.commit()
    db.refresh(db_device)
    
    return db_device




# ============== DEVICE PERMISSIONS ==============

@router.post("/users/{user_id}/devices/{device_id}/grant")
async def grant_permission(user_id: int, device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Grant user access to a device"""
    # Verify user exists
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify device exists
    device = crud.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Grant permission
    crud.grant_device_permission(db, user_id, device_id, admin.id)
    
    return {
        "message": f"Granted {user.username} access to {device.name}",
        "user_id": user_id,
        "device_id": device_id
    }


@router.delete("/users/{user_id}/devices/{device_id}/revoke")
async def revoke_permission(user_id: int, device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Revoke user access to a device"""
    success = crud.revoke_device_permission(db, user_id, device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    return {"message": "Permission revoked successfully"}


@router.get("/users/{user_id}/devices")
async def get_user_devices(user_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Get devices a user has access to"""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    devices = crud.get_user_devices(db, user_id)
    return {
        "username": user.username,
        "devices": devices,
        "count": len(devices)
    }


@router.get("/devices/{device_id}/users")
async def get_device_users(device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Get users with access to a device"""
    device = crud.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    users = crud.get_device_users(db, device_id)
    return {
        "device": device.name,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email
            }
            for u in users
        ],
        "count": len(users)
    }


# ============== IoT DEVICE MANAGEMENT (Admin) ==============

@router.get("/iot-devices")
async def get_all_iot_devices(admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin: Get device COUNT per user (NOT device details)"""
    from sqlalchemy import func
    
    # Get device count grouped by user
    device_counts = db.query(
        User.id,
        User.username,
        User.email,
        func.count(IoTDevice.id).label('device_count')
    ).outerjoin(IoTDevice, User.id == IoTDevice.user_id).group_by(
        User.id,
        User.username,
        User.email
    ).order_by(func.count(IoTDevice.id).desc()).all()
    
    result = []
    total_devices = 0
    for user_id, username, email, count in device_counts:
        result.append({
            "user_id": user_id,
            "username": username,
            "email": email,
            "device_count": count or 0
        })
        total_devices += (count or 0)
    
    return {
        "users_summary": result,
        "total_devices": total_devices,
        "total_users": len(result)
    }


@router.delete("/iot-devices/{device_id}")
async def delete_iot_device(device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin: Delete an IoT device completely"""
    device = db.query(IoTDevice).filter(IoTDevice.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IoT device not found"
        )
    
    user_id = device.user_id
    device_name = device.name
    
    db.delete(device)
    db.commit()
    
    return {
        "message": f"IoT device '{device_name}' deleted successfully",
        "user_id": user_id,
        "device_id": device_id
    }


@router.put("/iot-devices/{device_id}/disconnect")
async def disconnect_iot_device(device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin: Disconnect (deactivate) an IoT device from user"""
    device = db.query(IoTDevice).filter(IoTDevice.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IoT device not found"
        )
    
    device.is_active = False
    db.commit()
    db.refresh(device)
    
    return {
        "message": f"IoT device '{device.name}' disconnected from user",
        "device": {
            "id": device.id,
            "name": device.name,
            "is_active": device.is_active
        }
    }


@router.put("/iot-devices/{device_id}/reconnect")
async def reconnect_iot_device(device_id: int, admin: User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Admin: Reconnect (reactivate) an IoT device to user"""
    device = db.query(IoTDevice).filter(IoTDevice.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IoT device not found"
        )
    
    device.is_active = True
    db.commit()
    db.refresh(device)
    
    return {
        "message": f"IoT device '{device.name}' reconnected to user",
        "device": {
            "id": device.id,
            "name": device.name,
            "is_active": device.is_active
        }
    }
