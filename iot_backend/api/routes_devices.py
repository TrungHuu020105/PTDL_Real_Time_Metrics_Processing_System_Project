"""Device control routes (ESP32 relay + WiFi config)."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from iot_backend.state import runtime_state
from iot_backend import mqtt_service


router = APIRouter(prefix="/api/devices", tags=["devices"])


class ManualCommand(BaseModel):
    fan: Optional[bool] = None
    mist: Optional[bool] = None
    fog: Optional[bool] = None
    lamp: Optional[bool] = None
    auto: Optional[bool] = None


class WifiConfigRequest(BaseModel):
    ssid: str = Field(..., min_length=1, max_length=64)
    password: str = Field(default="", max_length=64)
    sensor_id: str = Field(default="esp32_devkit_v1", min_length=1, max_length=100)


@router.get("")
async def get_devices():
    return runtime_state.response()


@router.post("")
async def set_devices(payload: ManualCommand):
    runtime_state.set_manual(
        fan=payload.fan,
        mist=payload.mist,
        fog=payload.fog,
        lamp=payload.lamp,
        auto=payload.auto,
    )
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.post("/toggle-fan")
async def toggle_fan():
    runtime_state.set_fan_state(not runtime_state.devices.fan)
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.post("/toggle-fog")
async def toggle_fog():
    runtime_state.set_fog_state(not runtime_state.devices.fog)
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.post("/toggle-lamp")
async def toggle_lamp():
    runtime_state.devices.lamp = not runtime_state.devices.lamp
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.post("/auto-mode")
async def enable_auto_mode():
    runtime_state.devices.auto = True
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.post("/manual-mode")
async def enable_manual_mode():
    runtime_state.devices.auto = False
    response = runtime_state.response()
    mqtt_service.publish_commands("esp32_devkit_v1", response)
    return response


@router.get("/mqtt-status")
async def get_mqtt_status():
    return mqtt_service.status()


@router.post("/wifi-config")
async def update_wifi_config(payload: WifiConfigRequest):
    ok = mqtt_service.publish_wifi_config(
        sensor_id=payload.sensor_id,
        ssid=payload.ssid,
        password=payload.password,
    )
    if not ok:
        raise HTTPException(status_code=503, detail="MQTT unavailable, WiFi config not sent")
    return {"status": "sent", "sensor_id": payload.sensor_id, "ssid": payload.ssid}
