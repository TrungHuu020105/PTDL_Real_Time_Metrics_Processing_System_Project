"""API routes module"""
from . import routes_auth
from . import routes_admin
from . import routes_servers
from . import routes_chat

__all__ = [
    "routes_auth",
    "routes_admin",
    "routes_servers",
    "routes_chat",
]
