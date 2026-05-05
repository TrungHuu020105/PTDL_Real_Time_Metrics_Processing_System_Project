"""Server management routes - Admin creates, User subscribes"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AvailableServer, ServerSubscription, ServerSubscriptionRequest, User
from app.api.routes_auth import get_current_user
from app.system_metrics import SystemMetricsCollector
from app.config import METRICS_CENTRAL_BASE_URL, METRICS_CENTRAL_ADMIN_TOKEN
from app import crud
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
import json
import random
import time
import threading


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


class RejectRequestPayload(BaseModel):
    reason: Optional[str] = ""

    class Config:
        from_attributes = True

router = APIRouter(prefix="/api/servers", tags=["servers"])

_rent_lock = threading.Lock()
_rent_challenges = {}
_user_rentals = {}


def _fetch_remote_servers():
    url = f"{METRICS_CENTRAL_BASE_URL.rstrip('/')}/api/servers"
    req = urlrequest.Request(url, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
            data = json.loads(payload)
            if not isinstance(data, list):
                return []
            return data
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch remote servers: {str(exc)}"
        )


def _remote_json_request(method: str, path: str, payload: Optional[dict] = None, headers: Optional[dict] = None):
    url = f"{METRICS_CENTRAL_BASE_URL.rstrip('/')}{path}"
    body = None
    merged_headers = {"Content-Type": "application/json"}
    if headers:
        merged_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=body, headers=merged_headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = f"Remote API error HTTP {exc.code}"
        try:
            err = json.loads(exc.read().decode("utf-8"))
            if isinstance(err, dict) and err.get("detail"):
                detail = err["detail"]
        except Exception:
            pass
        raise HTTPException(status_code=exc.code if exc.code < 500 else status.HTTP_502_BAD_GATEWAY, detail=detail)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to connect remote API: {str(exc)}")


def _fetch_remote_server_history(server_id: str):
    url = f"{METRICS_CENTRAL_BASE_URL.rstrip('/')}/api/metrics/history?{urlencode({'server_id': server_id})}"
    req = urlrequest.Request(url, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
            data = json.loads(payload)
            if not isinstance(data, list):
                return []
            return data
    except HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found on metrics central API"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch remote server history: HTTP {exc.code}"
        )
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch remote server history: {str(exc)}"
        )


def _normalize_remote_server(item: dict):
    server_id = item.get("server_id")
    normalized_id = str(server_id) if server_id is not None else str(item.get("name", "unknown"))
    return {
        "id": normalized_id,
        "server_id": normalized_id,
        "name": item.get("name") or normalized_id,
        "specs": item.get("note") or (f"IP: {item.get('ip')}" if item.get("ip") else "Remote metrics source"),
        "cpu_cores": item.get("cpu_cores"),
        "cpu_physical_cores": item.get("cpu_physical_cores"),
        "ram_total_gb": item.get("ram_total_gb"),
        "ram_gb": item.get("ram_total_gb"),
        "os_type": item.get("os"),
        "os": item.get("os"),
        "architecture": item.get("architecture"),
        "is_available": True,
        "price_per_hour": 0.0,
        "subscribers_count": 0,
        "created_at": item.get("registered_at") or item.get("last_updated"),
        "registered_at": item.get("registered_at"),
        "cpu": item.get("cpu"),
        "ram": item.get("ram"),
        "disk": item.get("disk"),
        "ram_used_gb": item.get("ram_used_gb"),
        "ram_available_gb": item.get("ram_available_gb"),
        "uptime": item.get("uptime"),
        "ip": item.get("ip"),
        "status": item.get("status", "unknown"),
        "last_seen": item.get("last_seen"),
        "last_updated": item.get("last_updated"),
        "rented": item.get("rented", False),
    }


def _is_rental_visible_for_user(rental: dict, user: User) -> bool:
    return rental.get("user_id") == user.id or user.role == "admin"


def _serialize_rental_for_user(rental: dict, user: User):
    show_secret = user.role == "admin" or rental.get("user_id") == user.id
    return {
        "rental_id": rental.get("rental_id"),
        "server_id": rental.get("server_id"),
        "status": rental.get("status"),
        "created_at": rental.get("created_at"),
        "activated_at": rental.get("activated_at"),
        "cancelled_at": rental.get("cancelled_at"),
        "ip": rental.get("ip"),
        "port": rental.get("port"),
        "username": rental.get("username"),
        "ssh_command": rental.get("ssh_command"),
        "private_key_filename": rental.get("private_key_filename"),
        "private_key_available": show_secret and (not rental.get("private_key_downloaded", False)),
    }


class RentRequestBody(BaseModel):
    server_id: Optional[str] = None


class RentConfirmBody(BaseModel):
    challenge_id: str
    code: str


class CancelRentalBody(BaseModel):
    rental_id: str


@router.get("/{server_id}/history")
async def get_server_history(server_id: str):
    """Proxy server history from Metrics Central API."""
    history = _fetch_remote_server_history(server_id)
    return {
        "server_id": server_id,
        "history": history,
        "count": len(history),
    }


@router.post("/rent/request")
async def request_rent_code(
    body: RentRequestBody,
    current_user: User = Depends(get_current_user),
):
    """Create a 6-digit verification code before renting a server."""
    server_id = body.server_id
    if not server_id:
        raise HTTPException(status_code=422, detail="server_id is required")

    challenge_id = f"challenge_{random.randint(100000, 999999)}_{int(time.time())}"
    code = f"{random.randint(0, 999999):06d}"

    with _rent_lock:
        _rent_challenges[challenge_id] = {
            "challenge_id": challenge_id,
            "server_id": server_id,
            "user_id": current_user.id,
            "code": code,
            "created_at": time.time(),
            "expires_at": time.time() + 300,
            "used": False,
        }

    return {
        "challenge_id": challenge_id,
        "server_id": server_id,
        "verification_code": code,
        "expires_in_seconds": 300,
    }


@router.post("/rent/confirm")
async def confirm_rent(
    body: RentConfirmBody,
    current_user: User = Depends(get_current_user),
):
    """Validate code and create rental via central backend."""
    with _rent_lock:
        challenge = _rent_challenges.get(body.challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if challenge["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Challenge does not belong to current user")
        if challenge["used"]:
            raise HTTPException(status_code=400, detail="Challenge already used")
        if challenge["expires_at"] < time.time():
            raise HTTPException(status_code=400, detail="Challenge expired")
        if str(body.code).strip() != challenge["code"]:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        challenge["used"] = True
        server_id = challenge["server_id"]

    payload = {
        "server_id": server_id,
        "renter_name": current_user.username,
    }
    remote = _remote_json_request(
        "POST",
        "/api/rentals/create",
        payload=payload,
        headers={"x-admin-key": METRICS_CENTRAL_ADMIN_TOKEN},
    )

    rental_id = remote.get("rental_id")
    if not rental_id:
        raise HTTPException(status_code=500, detail="Remote rental response missing rental_id")

    record = {
        "rental_id": rental_id,
        "user_id": current_user.id,
        "server_id": remote.get("server_id") or server_id,
        "status": "active" if remote.get("message") == "VPS rented successfully" else remote.get("status", "pending"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "activated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) if remote.get("message") == "VPS rented successfully" else None,
        "ip": remote.get("ip"),
        "port": remote.get("port", 22),
        "username": remote.get("username"),
        "private_key_filename": remote.get("private_key_filename"),
        "private_key": remote.get("private_key"),
        "ssh_command": remote.get("ssh_command"),
        "private_key_downloaded": False,
    }

    with _rent_lock:
        _user_rentals[rental_id] = record

    return _serialize_rental_for_user(record, current_user)


@router.get("/my-rentals")
async def get_my_rentals(current_user: User = Depends(get_current_user)):
    with _rent_lock:
        items = [r for r in _user_rentals.values() if _is_rental_visible_for_user(r, current_user) and r.get("user_id") == current_user.id]
    return {"rentals": [_serialize_rental_for_user(r, current_user) for r in items], "total": len(items)}


@router.get("/rentals")
async def get_all_rentals(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action")
    with _rent_lock:
        items = list(_user_rentals.values())
    return {"rentals": [_serialize_rental_for_user(r, current_user) for r in items], "total": len(items)}


@router.get("/rentals/{rental_id}/private-key")
async def get_private_key_once(rental_id: str, current_user: User = Depends(get_current_user)):
    with _rent_lock:
        rental = _user_rentals.get(rental_id)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        if rental.get("user_id") != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not allowed")
        if rental.get("private_key_downloaded"):
            raise HTTPException(status_code=410, detail="Private key can only be downloaded once")
        private_key = rental.get("private_key")
        if not private_key:
            raise HTTPException(status_code=404, detail="Private key is not available")
        rental["private_key_downloaded"] = True
    return {
        "rental_id": rental_id,
        "private_key_filename": rental.get("private_key_filename"),
        "private_key": private_key,
    }


@router.post("/rentals/cancel")
async def cancel_rental(
    body: CancelRentalBody,
    current_user: User = Depends(get_current_user),
):
    with _rent_lock:
        rental = _user_rentals.get(body.rental_id)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        if rental.get("user_id") != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not allowed")

    remote = _remote_json_request(
        "POST",
        f"/api/rentals/{body.rental_id}/cancel",
        payload={},
        headers={"x-admin-key": METRICS_CENTRAL_ADMIN_TOKEN},
    )

    with _rent_lock:
        rental = _user_rentals.get(body.rental_id)
        if rental:
            rental["status"] = remote.get("status", "cancelled")
            rental["cancelled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return {"message": remote.get("message", "Rental cancelled"), "rental_id": body.rental_id, "status": remote.get("status", "cancelled")}


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
    remote_servers = _fetch_remote_servers()
    server_list = [_normalize_remote_server(s) for s in remote_servers]
    return {
        "servers": server_list,
        "total": len(server_list)
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
    remote_servers = _fetch_remote_servers()
    server_list = [_normalize_remote_server(s) for s in remote_servers]

    return {
        "servers": server_list,
        "total": len(server_list)
    }


@router.get("/{server_id}/subscribers")
async def get_server_subscribers(
    server_id: int,
    db: Session = Depends(get_db)
):
    """Get list of subscribers for a server"""
    return {
        "subscribers": [],
        "total": 0
    }


@router.post("/{server_id}/subscribe")
async def subscribe_to_server(
    server_id: int,
    subscription_duration_months: int = 1,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User subscribes to monitor a server"""
    from datetime import datetime, timezone, timedelta

    if subscription_duration_months not in [1, 3, 6, 12]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="subscription_duration_months must be 1, 3, 6, or 12"
        )

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

    vietnam_tz = timezone(timedelta(hours=7))
    now = datetime.now(vietnam_tz)
    expiration_date = now + timedelta(days=subscription_duration_months * 30)  # Approximate: 1 month = 30 days
    
    subscription = ServerSubscription(
        user_id=user.id,
        server_id=server_id,
        subscription_duration_months=subscription_duration_months,
        expiration_date=expiration_date
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "server_id": subscription.server_id,
        "subscribed_at": subscription.subscribed_at,
        "expiration_date": subscription.expiration_date,
        "subscription_duration_months": subscription.subscription_duration_months
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
    """Subscription model is disabled in remote-monitoring mode."""
    return {
        "servers": [],
        "total": 0
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
            "server_specs": server.specs if server else "Unknown",
            "subscription_duration_months": req.subscription_duration_months,
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
    reason: Optional[str] = None,
    payload: Optional[RejectRequestPayload] = Body(default=None),
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
    
    effective_reason = reason if reason is not None else (payload.reason if payload else "")

    # Use CRUD to reject
    rejected_req = crud.reject_subscription_request(db, request_id, effective_reason)
    
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
