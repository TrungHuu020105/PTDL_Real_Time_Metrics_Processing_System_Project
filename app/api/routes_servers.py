"""Server management routes - Admin creates, User subscribes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AvailableServer, ServerSubscription, User
from app.api.routes_auth import get_current_user

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
    servers = db.query(AvailableServer).all()
    
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
    """Get all servers the user is subscribed to"""
    subscriptions = db.query(ServerSubscription).filter(
        ServerSubscription.user_id == user.id
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
                "created_at": server.created_at
            })
    
    return {
        "servers": servers,
        "total": len(servers)
    }
