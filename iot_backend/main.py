"""IoT backend entrypoint (standalone service + ESP32 control)."""

import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iot_backend.config import get_cors_origins
from iot_backend.database import init_db, SessionLocal
from iot_backend.models import Metric
from iot_backend.api import (
    routes_auth,
    routes_iot_devices,
    routes_metrics,
    routes_alerts,
    routes_websocket,
    routes_admin_iot,
    routes_devices,
)
from iot_backend import mqtt_service
from iot_backend.state import runtime_state
from iot_backend.websocket_manager import manager


init_db()
MAIN_LOOP = None
VIETNAM_TZ = timezone(timedelta(hours=7))

app = FastAPI(
    title="IoT Backend Service",
    description="Standalone IoT service: metrics, alerts, realtime websocket, and IoT device management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
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
app.include_router(routes_devices.router)
app.include_router(routes_websocket.router, prefix="/api", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "service": "iot-backend",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.on_event("startup")
async def startup_event():
    """Initialize MQTT ingest for new ESP32 flow."""
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    try:
        mqtt_service.start_mqtt(on_reading=handle_mqtt_reading, on_device_state=None)
        print("[STARTUP] MQTT service started")
    except Exception as exc:
        print(f"[STARTUP] Failed to start MQTT service: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    mqtt_service.stop_mqtt()


def handle_mqtt_reading(reading: dict):
    """Handle both legacy metric payload and new temp/humidity payload."""
    db = SessionLocal()
    try:
        sensor_id = reading.get("sensor_id", "esp32_devkit_v1")
        location = reading.get("location") or "Unknown"
        now = datetime.now(VIETNAM_TZ)

        metric_type = reading.get("metric_type")
        metric_value = reading.get("value")
        temp = reading.get("temperature")
        humidity = reading.get("humidity")

        if metric_type is not None and metric_value is not None:
            db.add(
                Metric(
                    event_ts=now,
                    sensor_id=sensor_id,
                    location=location,
                    metric_type=str(metric_type),
                    metric_value=float(metric_value),
                    unit=reading.get("unit") or "",
                )
            )
        else:
            if temp is not None:
                db.add(
                    Metric(
                        event_ts=now,
                        sensor_id=sensor_id,
                        location=location,
                        metric_type="temperature",
                        metric_value=float(temp),
                        unit="°C",
                    )
                )
            if humidity is not None:
                db.add(
                    Metric(
                        event_ts=now,
                        sensor_id=sensor_id,
                        location=location,
                        metric_type="humidity",
                        metric_value=float(humidity),
                        unit="%",
                    )
                )
            if temp is not None and humidity is not None:
                runtime_state.apply_auto(float(temp), float(humidity))

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[SENSOR] Failed to save metrics: {exc}")
    finally:
        db.close()

    response = runtime_state.response()
    try:
        if MAIN_LOOP is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "sensor_update", "sensor": reading, "device_state": response}),
                MAIN_LOOP,
            )
    except Exception as exc:
        print(f"[WS] Broadcast skipped: {exc}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("iot_backend.main:app", host="0.0.0.0", port=8100, reload=True)
