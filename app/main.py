"""FastAPI application entry point"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.config import get_cors_origins
from app.api import routes_auth, routes_admin, routes_servers, routes_chat
from app.crud import get_user_by_username, create_user
from app.schemas import UserRegister
from app.api.routes_auth import hash_password

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="Real-Time Metrics Processing System",
    description="MVP backend for receiving, storing, and processing system metrics",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routes (core backend only)
app.include_router(routes_auth.router)
app.include_router(routes_admin.router)
app.include_router(routes_servers.router)
app.include_router(routes_chat.router)


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
    if str(os.getenv("ENABLE_DEMO_USERS", "false")).lower() != "true":
        return
    db = SessionLocal()
    try:
        # Create demo users if they don't exist
        admin_user = get_user_by_username(db, "admin")
        if not admin_user:
            admin_data = UserRegister(username="admin", email="admin@example.com", password="123456", role="admin")
            admin_user = create_user(db, admin_data, hash_password("123456"))
            print("[OK] [Startup] Created demo admin user (admin/123456)")
        
        user_user = get_user_by_username(db, "user")
        if not user_user:
            user_data = UserRegister(username="user", email="user@example.com", password="123456", role="user")
            user_user = create_user(db, user_data, hash_password("123456"))
            print("[OK] [Startup] Created demo user (user/123456)")
    except Exception as e:
        print(f"[ERROR] [Startup Error] {str(e)}")
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
