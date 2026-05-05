"""Application configuration"""

import os
from datetime import timedelta


def _load_dotenv():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            os.environ.setdefault(key, value)


_load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Remote Metrics Central API configuration
METRICS_CENTRAL_BASE_URL = os.getenv("METRICS_CENTRAL_BASE_URL", "http://localhost:9000")
METRICS_CENTRAL_TOKEN = os.getenv("METRICS_CENTRAL_TOKEN", "demo-secret-token")
METRICS_CENTRAL_ADMIN_TOKEN = os.getenv("METRICS_CENTRAL_ADMIN_TOKEN", "admin-demo-token")
