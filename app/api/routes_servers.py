"""Server management routes - Admin creates, User subscribes"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AvailableServer, ServerSubscription, ServerSubscriptionRequest, User
from app.api.routes_auth import get_current_user
from app.system_metrics import SystemMetricsCollector
from app import crud


# ============== REQUEST MODELS ==============
class ServerUpdateRequest(BaseModel):
    name: Optional[str] = None
    specs: Optional[str] = None
    price_per_hour: Optional[float] = None
    cpu_cores: Optional[int] = None
    ram_gb: Optional[int] = None
    os_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class SubscriptionRequestPayload(BaseModel):
    server_id: int
    subscription_duration_months: int = 1  # Duration in months: 1, 3, 6, or 12

    class Config:
        from_attributes = True

router = APIRouter(prefix="/api/servers", tags=["servers"])


def verify_admin(user: User = Depends(get_current_user)) -> User:
    """Verify that current user is admin"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return user


# ============== ADMIN: CREATE & MANAGE SERVERS ==============

@router.post("/admin/servers", dependencies=[Depends(verify_admin)])
async def create_server(
    name: str,
    specs: str,
    cpu_cores: int,
    ram_gb: int,
    os_type: str = "Ubuntu",
    price_per_hour: float = 0.0,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Create a new available server"""
    server = AvailableServer(
        name=name,
        specs=specs,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        os_type=os_type,
        price_per_hour=price_per_hour,
        created_by=admin.id,
        is_available=True
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    
    return {
        "id": server.id,
        "name": server.name,
        "specs": server.specs,
        "cpu_cores": server.cpu_cores,
        "ram_gb": server.ram_gb,
        "os_type": server.os_type,
        "is_available": server.is_available,
        "price_per_hour": server.price_per_hour,
        "created_at": server.created_at
    }


@router.get("/admin/servers", dependencies=[Depends(verify_admin)])
async def get_all_servers(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Get all servers"""
    print(f"[get_all_servers] Admin user: {admin.username}, ID: {admin.id}")
    servers = db.query(AvailableServer).all()
    print(f"[get_all_servers] Found {len(servers)} servers in database")
    
    # Count subscribers for each server
    server_list = []
    for server in servers:
        sub_count = db.query(ServerSubscription).filter(
            ServerSubscription.server_id == server.id
        ).count()
        
        server_list.append({
            "id": server.id,
            "name": server.name,
            "specs": server.specs,
            "cpu_cores": server.cpu_cores,
            "ram_gb": server.ram_gb,
            "os_type": server.os_type,
            "is_available": server.is_available,
            "price_per_hour": server.price_per_hour,
            "subscribers_count": sub_count,
            "created_at": server.created_at
        })
    
    print(f"[get_all_servers] Returning {len(server_list)} servers")
    return {
        "servers": server_list,
        "total": len(servers)
    }


@router.delete("/admin/servers/{server_id}", dependencies=[Depends(verify_admin)])
async def delete_server(
    server_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Delete a server"""
    server = db.query(AvailableServer).filter(AvailableServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Delete subscriptions first
    db.query(ServerSubscription).filter(ServerSubscription.server_id == server_id).delete()
    
    # Delete server
    db.delete(server)
    db.commit()
    
    return {"message": "Server deleted successfully"}


# ============== USER: BROWSE & SUBSCRIBE TO SERVERS ==============

@router.get("")
async def get_available_servers(db: Session = Depends(get_db)):
    """Get all available servers that users can subscribe to"""
    servers = db.query(AvailableServer).filter(AvailableServer.is_available == True).all()
    
    server_list = []
    for server in servers:
        sub_count = db.query(ServerSubscription).filter(
            ServerSubscription.server_id == server.id
        ).count()
        
        server_list.append({
            "id": server.id,
            "name": server.name,
            "specs": server.specs,
            "cpu_cores": server.cpu_cores,
            "ram_gb": server.ram_gb,
            "os_type": server.os_type,
            "is_available": server.is_available,
            "price_per_hour": server.price_per_hour,
            "subscribers_count": sub_count,
            "created_at": server.created_at
        })
    
    return {
        "servers": server_list,
        "total": len(servers)
    }


@router.get("/{server_id}/subscribers")
async def get_server_subscribers(
    server_id: int,
    db: Session = Depends(get_db)
):
    """Get list of subscribers for a server"""
    server = db.query(AvailableServer).filter(AvailableServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Get all subscriptions for this server
    subscriptions = db.query(ServerSubscription).filter(
        ServerSubscription.server_id == server_id
    ).all()
    
    subscribers = []
    for sub in subscriptions:
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user:
            subscribers.append({
                "username": user.username,
                "email": user.email,
                "subscribed_at": sub.subscribed_at,
                "expiration_date": sub.expiration_date,
                "subscription_duration_months": sub.subscription_duration_months
            })
    
    return {
        "subscribers": subscribers,
        "total": len(subscribers)
    }


@router.post("/{server_id}/subscribe")
async def subscribe_to_server(
    server_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User subscribes to monitor a server"""
    server = db.query(AvailableServer).filter(AvailableServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    if not server.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server is not available"
        )
    
    # Check if already subscribed
    existing = db.query(ServerSubscription).filter(
        ServerSubscription.user_id == user.id,
        ServerSubscription.server_id == server_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already subscribed to this server"
        )
    
    subscription = ServerSubscription(
        user_id=user.id,
        server_id=server_id
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "server_id": subscription.server_id,
        "subscribed_at": subscription.subscribed_at
    }


@router.delete("/{server_id}/unsubscribe")
async def unsubscribe_from_server(
    server_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User unsubscribes from a server"""
    subscription = db.query(ServerSubscription).filter(
        ServerSubscription.user_id == user.id,
        ServerSubscription.server_id == server_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    db.delete(subscription)
    db.commit()
    
    return {"message": "Unsubscribed successfully"}


# ============== USER: VIEW THEIR SUBSCRIPTIONS ==============

@router.get("/my-subscriptions")
async def get_my_subscriptions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all servers the user is subscribed to (excluding expired subscriptions)"""
    from datetime import datetime, timezone, timedelta
    
    vietnam_tz = timezone(timedelta(hours=7))
    now = datetime.now(vietnam_tz)
    
    subscriptions = db.query(ServerSubscription).filter(
        ServerSubscription.user_id == user.id,
        ServerSubscription.expiration_date > now  # Only active, non-expired subscriptions
    ).all()
    
    servers = []
    for sub in subscriptions:
        server = db.query(AvailableServer).filter(
            AvailableServer.id == sub.server_id
        ).first()
        
        if server:
            servers.append({
                "id": server.id,
                "name": server.name,
                "specs": server.specs,
                "cpu_cores": server.cpu_cores,
                "ram_gb": server.ram_gb,
                "os_type": server.os_type,
                "is_available": server.is_available,
                "price_per_hour": server.price_per_hour,
                "subscribed_at": sub.subscribed_at,
                "expiration_date": sub.expiration_date,
                "subscription_duration_months": sub.subscription_duration_months,
                "created_at": server.created_at
            })
    
    return {
        "servers": servers,
        "total": len(servers)
    }


# ============== USER: SERVER SUBSCRIPTION REQUESTS ==============

@router.post("/requests")
async def create_subscription_request(
    server_id: Optional[int] = None,
    duration_months: Optional[int] = None,
    payload: Optional[SubscriptionRequestPayload] = Body(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User creates a request to subscribe to a server with specified duration"""
    effective_server_id = server_id if server_id is not None else (payload.server_id if payload else None)
    effective_duration = duration_months if duration_months is not None else (payload.subscription_duration_months if payload else 1)

    if effective_server_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="server_id is required"
        )

    # Validate duration
    if effective_duration not in [1, 3, 6, 12]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="subscription_duration_months must be 1, 3, 6, or 12"
        )

    # Check if server exists
    server = db.query(AvailableServer).filter(AvailableServer.id == effective_server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Create subscription request using CRUD
    request = crud.create_subscription_request(db, user.id, effective_server_id, effective_duration)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create request - you may already have a pending request for this server"
        )
    
    return {
        "id": request.id,
        "user_id": request.user_id,
        "server_id": request.server_id,
        "subscription_duration_months": request.subscription_duration_months,
        "status": request.status,
        "requested_at": request.requested_at
    }


@router.get("/requests")
async def get_user_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User views their subscription requests"""
    requests = crud.get_user_subscription_requests(db, user.id)
    
    result = []
    for req in requests:
        # Get server info
        server = db.query(AvailableServer).filter(AvailableServer.id == req.server_id).first()
        result.append({
            "id": req.id,
            "server_id": req.server_id,
            "server_name": server.name if server else "Unknown",
            "status": req.status,
            "requested_at": req.requested_at,
            "approved_at": req.approved_at,
            "rejection_reason": req.rejection_reason
        })
    
    return {
        "requests": result,
        "total": len(result)
    }


# ============== ADMIN: MANAGE SUBSCRIPTION REQUESTS ==============

@router.get("/admin/requests/pending", dependencies=[Depends(verify_admin)])
async def get_pending_requests(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Get all pending subscription requests"""
    requests = crud.get_pending_subscription_requests(db)
    
    result = []
    for req in requests:
        # Get user and server info
        user = db.query(User).filter(User.id == req.user_id).first()
        server = db.query(AvailableServer).filter(AvailableServer.id == req.server_id).first()
        user_display_name = user.username if user else "Unknown"
        
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_email": user.email if user else "Unknown",
            "user_name": user_display_name,
            "server_id": req.server_id,
            "server_name": server.name if server else "Unknown",
            "server_specs": server.specs if server else "Unknown",
            "status": req.status,
            "requested_at": req.requested_at
        })
    
    return {
        "requests": result,
        "total": len(result)
    }


@router.put("/admin/requests/{request_id}/approve")
async def approve_request(
    request_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Approve a subscription request - also creates the subscription"""
    req = db.query(ServerSubscriptionRequest).filter(
        ServerSubscriptionRequest.id == request_id
    ).first()
    
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only approve pending requests, this is {req.status}"
        )
    
    # Use CRUD to approve
    approved_req = crud.approve_subscription_request(db, request_id, admin.id)
    
    return {
        "id": approved_req.id,
        "status": approved_req.status,
        "approved_at": approved_req.approved_at,
        "message": "Request approved and subscription created"
    }


@router.put("/admin/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    reason: str = "",
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Reject a subscription request"""
    req = db.query(ServerSubscriptionRequest).filter(
        ServerSubscriptionRequest.id == request_id
    ).first()
    
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only reject pending requests, this is {req.status}"
        )
    
    # Use CRUD to reject
    rejected_req = crud.reject_subscription_request(db, request_id, reason)
    
    return {
        "id": rejected_req.id,
        "status": rejected_req.status,
        "rejection_reason": rejected_req.rejection_reason,
        "message": "Request rejected"
    }


# ============== SYSTEM INFO ==============

@router.get("/admin/system-info", dependencies=[Depends(verify_admin)])
async def get_system_info(admin: User = Depends(verify_admin)):
    """[ADMIN] Get system hardware information (CPU cores, RAM, OS)"""
    system_info = SystemMetricsCollector.get_system_info()
    return {
        "cpu_cores": system_info["cpu_cores"],
        "ram_gb": system_info["ram_gb"],
        "os_type": system_info["os_type"]
    }


# ============== ADMIN: SET SERVER PRICE ==============

@router.put("/admin/servers/{server_id}/price")
async def set_server_price(
    server_id: int,
    price_per_hour: float,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Set the price of a server"""
    server = db.query(AvailableServer).filter(AvailableServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    if price_per_hour < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price cannot be negative"
        )
    
    server.price_per_hour = price_per_hour
    db.commit()
    db.refresh(server)
    
    return {
        "id": server.id,
        "name": server.name,
        "price_per_hour": server.price_per_hour,
        "message": "Price updated successfully"
    }


@router.patch("/admin/servers/{server_id}")
async def update_server(
    server_id: int,
    server_data: ServerUpdateRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """[ADMIN] Update server information (name, specs, price)"""
    server = db.query(AvailableServer).filter(AvailableServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Update only provided fields (not None)
    if server_data.name is not None:
        server.name = server_data.name
    if server_data.specs is not None:
        server.specs = server_data.specs
    if server_data.price_per_hour is not None:
        if server_data.price_per_hour < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price cannot be negative"
            )
        server.price_per_hour = server_data.price_per_hour
    if server_data.cpu_cores is not None:
        server.cpu_cores = server_data.cpu_cores
    if server_data.ram_gb is not None:
        server.ram_gb = server_data.ram_gb
    if server_data.os_type is not None:
        server.os_type = server_data.os_type
    
    db.commit()
    db.refresh(server)
    
    return {
        "id": server.id,
        "name": server.name,
        "specs": server.specs,
        "cpu_cores": server.cpu_cores,
        "ram_gb": server.ram_gb,
        "os_type": server.os_type,
        "price_per_hour": server.price_per_hour,
        "message": "Server updated successfully"
    }
