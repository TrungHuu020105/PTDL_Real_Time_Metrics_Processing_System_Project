"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.api import routes_metrics, routes_alerts, routes_auth
from app.crud import delete_old_alerts, get_user_by_username, create_user
from app.schemas import UserRegister
from app.api.routes_auth import hash_password

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
            create_user(db, admin_data, hash_password("123456"))
            print("✓ [Startup] Created demo admin user (admin/123456)")
        
        user_user = get_user_by_username(db, "user")
        if not user_user:
            user_data = UserRegister(username="user", email="user@example.com", password="123456", role="user")
            create_user(db, user_data, hash_password("123456"))
            print("✓ [Startup] Created demo user (user/123456)")
            
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
