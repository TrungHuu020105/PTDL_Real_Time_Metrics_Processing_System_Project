"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.api import routes_metrics, routes_alerts, routes_auth, routes_admin
from app.crud import delete_old_alerts, get_user_by_username, create_user
from app.schemas import UserRegister
from app.api.routes_auth import hash_password
from app.models import Device, UserDevicePermission

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="Real-Time Metrics Processing System",
    description="MVP backend for receiving, storing, and processing system metrics",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes_metrics.router)
app.include_router(routes_alerts.router)
app.include_router(routes_auth.router)
app.include_router(routes_admin.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Real-Time Metrics Processing System API",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on server startup"""
    db = SessionLocal()
    try:
        # Clean up old alerts
        deleted = delete_old_alerts(db, days=15)
        print(f"✓ [Startup] Cleaned up {deleted} alerts older than 15 days")
        
        # Create demo users if they don't exist
        admin_user = get_user_by_username(db, "admin")
        if not admin_user:
            admin_data = UserRegister(username="admin", email="admin@example.com", password="123456", role="admin")
            admin_user = create_user(db, admin_data, hash_password("123456"))
            print("✓ [Startup] Created demo admin user (admin/123456)")
        
        user_user = get_user_by_username(db, "user")
        if not user_user:
            user_data = UserRegister(username="user", email="user@example.com", password="123456", role="user")
            user_user = create_user(db, user_data, hash_password("123456"))
            print("✓ [Startup] Created demo user (user/123456)")
        
        # Create demo devices if they don't exist
        demo_devices = [
            {"name": "System Monitor", "device_type": "cpu", "source": "system_monitor", "location": "Local"},
            {"name": "Sensor 1", "device_type": "temperature", "source": "sensor_1", "location": "Room 1"},
            {"name": "Sensor 2", "device_type": "humidity", "source": "sensor_2", "location": "Room 2"},
            {"name": "Sensor 3", "device_type": "soil_moisture", "source": "sensor_3", "location": "Garden"},
            {"name": "Sensor 4", "device_type": "light_intensity", "source": "sensor_4", "location": "Office"},
        ]
        
        for demo_device in demo_devices:
            existing = db.query(Device).filter(Device.source == demo_device["source"]).first()
            if not existing:
                device = Device(
                    name=demo_device["name"],
                    device_type=demo_device["device_type"],
                    source=demo_device["source"],
                    location=demo_device["location"],
                    is_active=True,
                    created_by=admin_user.id
                )
                db.add(device)
                db.commit()
                db.refresh(device)
                
                # Grant admin access to all demo devices
                permission = UserDevicePermission(
                    user_id=admin_user.id,
                    device_id=device.id,
                    granted_by=admin_user.id
                )
                db.add(permission)
                db.commit()
                print(f"✓ [Startup] Created demo device: {demo_device['name']}")
            
    except Exception as e:
        print(f"✗ [Startup Error] {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
