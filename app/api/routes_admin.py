"""Admin management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import DeviceCreate, DeviceResponse, UserResponse
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
