"""
WebSocket routes for real-time IoT metrics streaming.
"""

import asyncio
import json
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from iot_backend.config import ALGORITHM, SECRET_KEY
from iot_backend.crud import create_alert, create_metrics_bulk, get_user_accessible_sources, get_user_by_username
from iot_backend.database import SessionLocal
from iot_backend.models import IoTDevice
from iot_backend.schemas import AlertCreate, MetricCreate
from iot_backend.schemas_ws import IotMetricsData, MetricsData, StatusResponse
from iot_backend.services.alert_service import dispatch_alert_notifications
from iot_backend.websocket_manager import ConnectionManager

router = APIRouter(tags=["WebSocket Metrics"])

manager = ConnectionManager()
ALERT_NOTIFY_COOLDOWN_SECONDS = 5
_last_alert_notification_ts = {}


def _decode_ws_token(token: str | None):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        db = SessionLocal()
        try:
            user = get_user_by_username(db, username)
            if not user or not user.is_active:
                return None
            return {
                "user_id": user.id,
                "role": user.role,
                "username": user.username,
            }
        finally:
            db.close()
    except JWTError:
        return None


def _can_receive_source(connection_info: dict, source: str) -> bool:
    metadata = connection_info.get("metadata") or {}
    user_id = metadata.get("user_id")
    role = metadata.get("role")
    if not user_id:
        # Unauthenticated clients are publishers-only.
        return False
    if role == "admin":
        return True

    db = SessionLocal()
    try:
        allowed_sources = set(get_user_accessible_sources(db, int(user_id)))
    finally:
        db.close()
    return source in allowed_sources


def _parse_metric_timestamp(timestamp: str | None) -> datetime:
    if not timestamp:
        return datetime.now()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return parsed.astimezone().replace(tzinfo=None)
        return parsed
    except Exception:
        return datetime.now()


def _check_and_trigger_alert(db, metric_type: str, source: str, value: float, metric_ts: datetime):
    try:
        device = db.query(IoTDevice).filter(IoTDevice.source == source).first()
    except Exception as exc:
        print(f"[ALERT] Failed to query IoTDevice for source={source}: {exc}")
        return

    if not device:
        return

    has_thresholds = device.lower_threshold is not None or device.upper_threshold is not None
    if not device.alert_enabled and not has_thresholds:
        return

    threshold = None
    status = None
    if device.upper_threshold is not None and value > device.upper_threshold:
        threshold = device.upper_threshold
        status = "critical"
    elif device.lower_threshold is not None and value < device.lower_threshold:
        threshold = device.lower_threshold
        status = "warning"

    alert_key = f"{source}:{metric_type}"

    if threshold is None or status is None:
        _last_alert_notification_ts.pop(alert_key, None)
        return

    now_ts = time.time()
    last_ts = _last_alert_notification_ts.get(alert_key, 0)
    if now_ts - last_ts < ALERT_NOTIFY_COOLDOWN_SECONDS:
        return

    try:
        alert = create_alert(
            db,
            AlertCreate(
                metric_type=metric_type,
                status=status,
                current_value=value,
                threshold=float(threshold),
                message=f"{metric_type} threshold exceeded on {device.name}",
                source=source,
                created_at=metric_ts,
            ),
        )
    except Exception as exc:
        print(f"[ALERT] Failed to create alert for {source}/{metric_type}: {exc}")
        return

    _last_alert_notification_ts[alert_key] = now_ts
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(dispatch_alert_notifications(alert.id))
    except RuntimeError:
        pass


def save_iot_metric_to_db(
    metric_type: str,
    source: str,
    location: str | None,
    timestamp: str | None,
    value: float,
    unit: str,
    save_flag: bool,
):
    with open("backend_filtering.log", "a", encoding="utf-8") as f:
        f.write(f"{metric_type}={value} | saved={save_flag}\n")

    db = None
    try:
        db = SessionLocal()
        metric_ts = _parse_metric_timestamp(timestamp)
        _check_and_trigger_alert(db, metric_type, source, value, metric_ts)

        if not save_flag:
            return

        metric = MetricCreate(
            event_ts=timestamp,
            sensor_id=source,
            location=location,
            metric_type=metric_type,
            metric_value=value,
            unit=unit,
        )
        create_metrics_bulk(db, [metric])
    except Exception as e:
        print(f"DB save error: {e}")
    finally:
        if db:
            db.close()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint:
    - Authenticated viewers connect with ?token=<JWT> and receive filtered realtime stream.
    - Publishers can connect without token and push metrics payloads.
    """
    try:
        ws_token = websocket.query_params.get("token")
        principal = _decode_ws_token(ws_token)
        metadata = principal or {"connection_mode": "publisher_only"}

        await manager.connect(client_id, websocket, metadata=metadata)

        while True:
            data = await websocket.receive_text()
            metrics_dict = json.loads(data)

            if "metric_type" in metrics_dict:
                try:
                    metrics = IotMetricsData(**metrics_dict)
                    manager.save_metrics(client_id, metrics.model_dump())

                    realtime_broadcast = {
                        "type": "iot_metric",
                        "metric_type": metrics.metric_type,
                        "value": metrics.value,
                        "source": metrics.source,
                        "timestamp": metrics.timestamp or datetime.now().isoformat(),
                        "saved": metrics.saved,
                    }

                    broadcast_payload = json.dumps(realtime_broadcast)
                    for target_client_id, info in list(manager.active_connections.items()):
                        if _can_receive_source(info, metrics.source):
                            await manager.send_to_client(target_client_id, broadcast_payload)

                    save_iot_metric_to_db(
                        metrics.metric_type,
                        metrics.source,
                        metrics.location,
                        metrics.timestamp,
                        metrics.value,
                        metrics.unit,
                        metrics.saved,
                    )

                    await websocket.send_text(
                        json.dumps(
                            {
                                "status": "ok",
                                "message": f"IoT metric received: {metrics.metric_type}",
                                "server_time": datetime.now().isoformat(),
                            }
                        )
                    )
                except ValueError as e:
                    await websocket.send_text(
                        json.dumps({"status": "error", "message": f"IoT Validation error: {str(e)}"})
                    )
            else:
                try:
                    metrics = MetricsData(**metrics_dict)
                    manager.save_metrics(client_id, metrics.model_dump())
                    await websocket.send_text(
                        json.dumps(
                            {
                                "status": "ok",
                                "message": f"System metrics received from {client_id}",
                                "server_time": datetime.now().isoformat(),
                            }
                        )
                    )
                except ValueError as e:
                    await websocket.send_text(
                        json.dumps({"status": "error", "message": f"System Validation error: {str(e)}"})
                    )

    except json.JSONDecodeError as e:
        await websocket.send_text(json.dumps({"status": "error", "message": f"Invalid JSON format: {str(e)}"}))
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error with client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status():
    return manager.get_all_status()


@router.get("/status/{client_id}", tags=["Status"])
async def get_client_status(client_id: str):
    client_info = manager.get_client_info(client_id)
    if client_info is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client_info


@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "WebSocket Metrics Server is running",
        "connected_clients": len(manager.active_connections),
        "timestamp": datetime.now().isoformat(),
    }

