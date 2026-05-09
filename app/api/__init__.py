"""API routes module"""
from . import routes_metrics
from . import routes_alerts
from . import routes_auth
from . import routes_admin
from . import routes_websocket
from . import routes_iot_devices
from . import routes_servers
from . import routes_chat

__all__ = [
    "routes_metrics",
    "routes_alerts", 
    "routes_auth",
    "routes_admin",
    "routes_websocket",
    "routes_iot_devices",
    "routes_servers",
    "routes_chat",
]
