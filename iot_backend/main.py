"""IoT backend entrypoint (standalone service)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iot_backend.database import init_db
from iot_backend.api import routes_auth, routes_iot_devices, routes_metrics, routes_alerts, routes_websocket, routes_admin_iot


init_db()

app = FastAPI(
    title="IoT Backend Service",
    description="Standalone IoT service: metrics, alerts, realtime websocket, and IoT device management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(routes_metrics.router)
app.include_router(routes_alerts.router)
app.include_router(routes_auth.router)
app.include_router(routes_admin_iot.router)
app.include_router(routes_iot_devices.router)
app.include_router(routes_websocket.router, prefix="/api", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "service": "iot-backend",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("iot_backend.main:app", host="0.0.0.0", port=8100, reload=True)

