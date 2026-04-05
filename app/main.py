"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.api import routes_metrics, routes_alerts
from app.crud import delete_old_alerts

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
    """Clean up old alerts when server starts"""
    db = SessionLocal()
    try:
        deleted = delete_old_alerts(db, days=15)
        print(f"✓ [Startup] Cleaned up {deleted} alerts older than 15 days")
    except Exception as e:
        print(f"✗ [Startup Error] Failed to cleanup alerts: {str(e)}")
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
